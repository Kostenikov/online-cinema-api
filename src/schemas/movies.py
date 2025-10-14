from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    year: int
    time: int = Field(ge=1)
    imdb: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(ge=0)

    model_config = {"from_attributes": True}

    @field_validator("year")
    @classmethod
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot exceed {current_year + 1}")
        return value


class MovieDetail(MovieBaseSchema):
    id: int
    uuid: str
    certification: CertificationSchema
    genres: list[GenreSchema]
    directors: list[DirectorSchema]
    stars: list[StarSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    description: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[int]
    next_page: Optional[int]
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str
    year: int
    time: int = Field(ge=1)
    imdb: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(ge=0)
    certification_id: int
    genres: list[str]
    directors: list[str]
    stars: list[str]

    model_config = {"from_attributes": True}

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: list[str]) -> list[str]:
        return [item.title() for item in value]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = Field(None, ge=0, le=10)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)

    model_config = {"from_attributes": True}
