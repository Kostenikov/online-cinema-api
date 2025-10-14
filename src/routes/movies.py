from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import CertificationModel, DirectorModel, GenreModel, MovieModel, StarModel, UserModel, get_db
from repository.movies import (
    get_movie,
    get_movie_or_404,
    get_movies,
    get_number_of_movies,
    get_or_create,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetail,
    MovieListResponseSchema,
    MovieUpdateSchema,
)
from security.permissions import require_admin, require_moderator, require_user

router = APIRouter()


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    responses={404: {"description": "No movies found."}},
)
async def list_movies(
    current_user: Annotated[UserModel, Depends(require_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):

    movies = await get_movies(per_page, page, db)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await get_number_of_movies(db)
    total_pages = (total_items - 1) // per_page + 1
    prev_page = f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieDetail,
    responses={409: {"description": "Movie already exists."}},
)
async def create_movie(
    current_user: Annotated[UserModel, Depends(require_moderator)],
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):

    movie_exists = await get_movie(
        db=db,
        name=movie.name,
        year=movie.year,
        time=movie.time,
    )
    if movie_exists:
        raise HTTPException(status_code=409, detail=f"Movie '{movie.name}' ({movie.year}) already exists.")

    certification = await get_or_create(CertificationModel, db, id=movie.certification_id)

    genres = [await get_or_create(GenreModel, db, name=name) for name in movie.genres]
    directors = [await get_or_create(DirectorModel, db, name=name) for name in movie.directors]
    stars = [await get_or_create(StarModel, db, name=name) for name in movie.stars]

    new_movie = MovieModel(
        name=movie.name,
        year=movie.year,
        time=movie.time,
        imdb=movie.imdb,
        votes=movie.votes,
        meta_score=movie.meta_score,
        gross=movie.gross,
        description=movie.description,
        price=movie.price,
        certification=certification,
        genres=genres,
        directors=directors,
        stars=stars,
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    full_movie = await get_movie(db, id=new_movie.id)
    return MovieDetail.model_validate(full_movie)


@router.get(
    "/{movie_id}/",
    response_model=MovieDetail,
    responses={404: {"description": "Movie not found."}},
)
async def movie_detail(
    current_user: Annotated[UserModel, Depends(require_user)],
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await get_movie_or_404(movie_id, db)
    return MovieDetail.model_validate(movie)


@router.delete(
    "/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Movie not found."}},
)
async def delete_movie(
    current_user: Annotated[UserModel, Depends(require_moderator)],
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await get_movie_or_404(movie_id, db)
    await db.delete(movie)
    await db.commit()


@router.patch(
    "/{movie_id}/",
    response_model=dict,
    responses={400: {"description": "Invalid data."}, 404: {"description": "Movie not found."}},
)
async def update_movie(
    current_user: Annotated[UserModel, Depends(require_moderator)],
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):

    movie = await get_movie_or_404(movie_id, db)
    data = movie_data.model_dump(exclude_unset=True)

    try:
        for field, value in data.items():
            setattr(movie, field, value)
        await db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
