import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

movie_genres = Table(
    "movies_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "director_id",
        ForeignKey("directors.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

movie_stars = Table(
    "stars_movies",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "star_id",
        ForeignKey("stars.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=movie_genres,
        back_populates="genres",
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", secondary=movie_directors, back_populates="directors"
    )

    def __repr__(self):
        return f"<Director(name='{self.name}')>"


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=movie_stars,
        back_populates="stars",
    )

    def __repr__(self):
        return f"<Star(name='{self.name}')>"


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="certification")


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    certification: Mapped["CertificationModel"] = relationship(
        "CertificationModel",
        back_populates="movies",
    )

    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel",
        secondary=movie_genres,
        back_populates="movies",
    )

    stars: Mapped[list["StarModel"]] = relationship(
        "StarModel",
        secondary=movie_stars,
        back_populates="movies",
    )

    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel", secondary=movie_directors, back_populates="movies"
    )

    comments: Mapped[list["CommentModel"]] = relationship(
        "CommentModel", back_populates="movie", cascade="all, delete"
    )

    __table_args__ = (UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),)

    def __repr__(self):
        return f"<Movie(name='{self.name}', year={self.year}, score={self.meta_score})>"


class ReactionTypeEnum(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    object_id: Mapped[int] = mapped_column(nullable=False)
    reaction_type: Mapped[ReactionTypeEnum] = mapped_column(Enum(ReactionTypeEnum), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "content_type", "object_id"),)


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="comments")  # noqa: F821
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="comments")
