from typing import Sequence, TypeVar

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import Base, GenreModel, MovieModel, Reaction, ReactionTypeEnum, StarModel

T = TypeVar("T", bound=Base)


async def get_movies(per_page: int, page: int, db: AsyncSession) -> Sequence[MovieModel]:
    movies = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    return movies.scalars().all()


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
