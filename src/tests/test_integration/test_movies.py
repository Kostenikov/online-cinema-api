from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import CertificationModel, DirectorModel, GenreModel, StarModel, UserModel
from src.routes.movies import update_movie
from src.schemas.movies import MovieUpdateSchema


@pytest.mark.asyncio
async def test_update_movie_success():
    mock_user = MagicMock(spec=UserModel)
    mock_movie = MagicMock()
    mock_db = MagicMock(spec=AsyncSession)
    mock_movie_data = MovieUpdateSchema(name="New Movie Name")
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    mock_movie_or_404 = AsyncMock(return_value=mock_movie)
    mock_get_or_create = AsyncMock()

    with pytest.MonkeyPatch().context() as monkeypatch:
        monkeypatch.setattr("src.routes.movies.get_movie_or_404", mock_movie_or_404)
        monkeypatch.setattr("src.routes.movies.get_or_create", mock_get_or_create)
        response = await update_movie(mock_user, 1, mock_movie_data, mock_db)

    mock_movie_or_404.assert_called_once_with(1, mock_db)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_movie)
    assert response == {"detail": "Movie updated successfully."}


@pytest.mark.asyncio
async def test_update_movie_not_found():
    mock_user = MagicMock(spec=UserModel)
    mock_db = MagicMock(spec=AsyncSession)
    mock_movie_data = MovieUpdateSchema(name="Nonexistent Movie")

    mock_movie_or_404 = AsyncMock(
        side_effect=HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    )

    with pytest.MonkeyPatch().context() as monkeypatch:
        monkeypatch.setattr("src.routes.movies.get_movie_or_404", mock_movie_or_404)

        with pytest.raises(HTTPException) as exc_info:
            await update_movie(mock_user, 99, mock_movie_data, mock_db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Movie with the given ID was not found."


@pytest.mark.asyncio
async def test_update_movie_invalid_data():
    mock_user = MagicMock(spec=UserModel)
    mock_movie = MagicMock()
    mock_db = MagicMock(spec=AsyncSession)
    mock_movie_data = MovieUpdateSchema(imdb=-5)

    mock_movie_or_404 = AsyncMock(return_value=mock_movie)

    with pytest.MonkeyPatch().context() as monkeypatch:
        monkeypatch.setattr("src.routes.movies.get_movie_or_404", mock_movie_or_404)

        with pytest.raises(HTTPException) as exc_info:
            await update_movie(mock_user, 1, mock_movie_data, mock_db)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid input data."


@pytest.mark.asyncio
async def test_update_movie_certifications_and_genres():
    mock_user = MagicMock(spec=UserModel)
    mock_movie = MagicMock()
    mock_db = MagicMock(spec=AsyncSession)
    mock_movie_data = MovieUpdateSchema(certification="PG-13", genres=["Action", "Drama"])

    mock_movie_or_404 = AsyncMock(return_value=mock_movie)
    mock_get_or_create = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with pytest.MonkeyPatch().context() as monkeypatch:
        monkeypatch.setattr("src.routes.movies.get_movie_or_404", mock_movie_or_404)
        monkeypatch.setattr("src.routes.movies.get_or_create", mock_get_or_create)
        response = await update_movie(mock_user, 1, mock_movie_data, mock_db)

    mock_movie_or_404.assert_called_once_with(1, mock_db)
    mock_get_or_create.assert_any_call(CertificationModel, mock_db, name="PG-13")
    mock_get_or_create.assert_any_call(GenreModel, mock_db, name="Action")
    mock_get_or_create.assert_any_call(GenreModel, mock_db, name="Drama")
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_movie)
    assert response == {"detail": "Movie updated successfully."}
