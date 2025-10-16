from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreateSchema(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    content: str
    created_at: datetime
    likes: int = 0
    dislikes: int = 0
    user_reaction: Optional[str] = None


class NameBase(BaseModel):
    name: str = Field(max_length=255)


class GenreCreate(NameBase):
    pass


class GenreUpdate(BaseModel):
    name: str | None = None


class GenreDetail(NameBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    movie_count: int = 0


class StarCreate(NameBase):
    pass


class StarUpdate(BaseModel):
    name: str | None = None


class StarDetail(NameBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DirectorSchema(NameBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CertificationSchema(NameBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=255)
    year: int
    time: int = Field(ge=1)
    imdb: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(ge=0)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot exceed {current_year + 1}")
        return value


class MovieDetail(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    certification: CertificationSchema
    likes: int = 0
    dislikes: int = 0
    user_reaction: Optional[str] = None
    genres: list[GenreDetail]
    directors: list[DirectorSchema]
    stars: list[StarDetail]


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    year: int
    imdb: float
    description: str
    likes: int = 0
    dislikes: int = 0
    user_reaction: Optional[str] = None


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=255)
    year: int
    time: int = Field(ge=1)
    imdb: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(ge=0)
    certification: str
    genres: list[str]
    directors: list[str]
    stars: list[str]

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: list[str]) -> list[str]:
        return [item.title() for item in value]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = Field(None, ge=1)
    imdb: Optional[float] = None
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    certification: Optional[str] = None
    genres: Optional[list[str]] = None
    directors: Optional[list[str]] = None
    stars: Optional[list[str]] = None
