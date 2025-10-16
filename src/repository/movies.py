from typing import Optional, Sequence, TypeVar

from fastapi import HTTPException
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import Base, CommentModel, DirectorModel, GenreModel, MovieModel, Reaction, ReactionTypeEnum, StarModel

T = TypeVar("T", bound=Base)


async def get_movies(
    per_page: int,
    page: int,
    db: AsyncSession,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    imdb_min: Optional[float] = None,
    imdb_max: Optional[float] = None,
    votes_min: Optional[int] = None,
    votes_max: Optional[int] = None,
    meta_score_min: Optional[float] = None,
    meta_score_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
) -> Sequence[MovieModel]:
    query = select(MovieModel)

    query = query.options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.directors),
        joinedload(MovieModel.stars),
        joinedload(MovieModel.certification),
    )

    if genre_id is not None:
        query = query.join(MovieModel.genres).where(GenreModel.id == genre_id)
    if year_from is not None:
        query = query.where(MovieModel.year >= year_from)
    if year_to is not None:
        query = query.where(MovieModel.year <= year_to)
    if imdb_min is not None:
        query = query.where(MovieModel.imdb >= imdb_min)
    if imdb_max is not None:
        query = query.where(MovieModel.imdb <= imdb_max)
    if votes_min is not None:
        query = query.where(MovieModel.votes >= votes_min)
    if votes_max is not None:
        query = query.where(MovieModel.votes <= votes_max)
    if meta_score_min is not None:
        query = query.where(MovieModel.meta_score >= meta_score_min)
    if meta_score_max is not None:
        query = query.where(MovieModel.meta_score <= meta_score_max)

    if sort_by:
        sort_by = sort_by.lower()
        if sort_by in MovieModel.__table__.columns.keys():
            column = getattr(MovieModel, sort_by)
            query = query.order_by(desc(column) if sort_order == "desc" else asc(column))
        else:
            query = query.order_by(MovieModel.id.desc())
    else:
        query = query.order_by(MovieModel.id.desc())

    if search:
        search_pattern = f"%{search}%"
        query = (
            query.join(MovieModel.stars, isouter=True)
            .join(MovieModel.directors, isouter=True)
            .join(MovieModel.genres, isouter=True)
        )
        query = query.where(
            or_(
                MovieModel.name.ilike(search_pattern),
                MovieModel.description.ilike(search_pattern),
                StarModel.name.ilike(search_pattern),
                GenreModel.name.ilike(search_pattern),
                DirectorModel.name.ilike(search_pattern),
            )
        )

    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return result.unique().scalars().all()


async def get_number_of_movies(db: AsyncSession) -> int:
    return (await db.execute(select(func.count()).select_from(MovieModel))).scalar()


async def get_movie(db: AsyncSession, **kwargs) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.stars),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.certification),
        )
        .filter_by(**kwargs)
    )
    return result.unique().scalar_one_or_none()


async def get_or_create(db_model: type[T], db: AsyncSession, **kwargs) -> T:
    result = await db.execute(select(db_model).filter_by(**kwargs))

    if db_record := result.unique().scalar_one_or_none():
        return db_record

    new_record = db_model(**kwargs)
    db.add(new_record)
    await db.flush()

    return new_record


async def get_movie_or_404(movie_id: int, db: AsyncSession) -> MovieModel:

    if movie := await get_movie(db, id=movie_id):
        return movie

    raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")


async def get_genres(db: AsyncSession):
    result = await db.execute(select(GenreModel))
    return result.scalars().all()


async def get_genre_or_404(genre_id: int, db: AsyncSession):
    result = await db.execute(select(GenreModel).filter_by(id=genre_id))
    genre = result.scalar_one_or_none()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return genre


async def get_stars(db: AsyncSession):
    result = await db.execute(select(StarModel))
    return result.scalars().all()


async def get_star_or_404(star_id: int, db: AsyncSession):
    result = await db.execute(select(StarModel).filter_by(id=star_id))
    star = result.scalar_one_or_none()
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    return star


async def toggle_reaction(db, user_id, content_type, object_id, action: ReactionTypeEnum):
    stmt = select(Reaction).filter_by(user_id=user_id, content_type=content_type, object_id=object_id)
    result = await db.execute(stmt)
    reaction = result.scalar_one_or_none()

    if reaction:
        if reaction.reaction_type == action:
            await db.delete(reaction)
            await db.commit()
            return {"detail": "Reaction removed."}
        else:
            reaction.reaction_type = action
            await db.commit()
            await db.refresh(reaction)
            return {"detail": f"Reaction changed to {action.value}."}
    else:
        new_reaction = Reaction(
            user_id=user_id,
            content_type=content_type,
            object_id=object_id,
            reaction_type=action,
        )
        db.add(new_reaction)
        await db.commit()
        return {"detail": f"{action.value.capitalize()} added."}


async def get_genres_with_movie_count(db: AsyncSession) -> list[dict]:
    query = (
        select(GenreModel.id, GenreModel.name, func.count(MovieModel.id).label("movie_count"))
        .join(MovieModel.genres, isouter=True)
        .group_by(GenreModel.id)
    )
    result = await db.execute(query)

    genres = []
    for res in result.all():
        genres.append(
            {
                "id": res.id,
                "name": res.name,
                "movie_count": res.movie_count,
                "movies_url": f"/movies/?genre_id={res.id}",
            }
        )
    return genres


async def get_movies_by_genre(genre_id: int, db: AsyncSession) -> Sequence[MovieModel]:
    query = (
        select(MovieModel)
        .join(MovieModel.genres)
        .where(GenreModel.id == genre_id)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.stars),
            joinedload(MovieModel.certification),
        )
        .order_by(MovieModel.id.desc())
    )
    result = await db.execute(query)
    return result.unique().scalars().all()


async def add_comment(db: AsyncSession, user_id: int, movie_id: int, content: str):
    comment = CommentModel(user_id=user_id, movie_id=movie_id, content=content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_movie_comments(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(CommentModel).where(CommentModel.movie_id == movie_id).order_by(CommentModel.created_at.desc())
    )
    return result.scalars().all()


async def get_comment_or_404(comment_id: int, db: AsyncSession) -> CommentModel:
    result = await db.execute(select(CommentModel).where(CommentModel.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    return comment


async def get_comment_reaction_counts(db: AsyncSession, comment_id: int):
    stmt = (
        select(Reaction.reaction_type, func.count(Reaction.id))
        .where(Reaction.content_type == "comment", Reaction.object_id == comment_id)
        .group_by(Reaction.reaction_type)
    )
    result = await db.execute(stmt)
    counts = dict(result.all())
    return {"likes": counts.get(ReactionTypeEnum.LIKE, 0), "dislikes": counts.get(ReactionTypeEnum.DISLIKE, 0)}
