from dataclasses import dataclass
from uuid import UUID

from multidict import CIMultiDictProxy
from pydantic import BaseModel


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


class PersonBase(BaseModel):
    """Базовый набор полей персоны"""
    full_name: str
    role: str


class PersonScheme(PersonBase):
    """Модель для валидации данных персоны от api"""
    uuid: UUID
    film_ids: list[str]


class PersonModel(PersonBase):
    """Модель для валидации данных персоны из кеша"""
    id: str
    films_ids: list[str]


class PersonShortInfo(BaseModel):
    id: str
    name: str


class FilmSchema(BaseModel):
    """Полный набор полей для эндпоинта с описанием одного фильма"""
    uuid: UUID
    title: str
    imdb_rating: float
    genre: list[str] | None
    description: str | None
    directors: list[str] | None
    actors: list[PersonShortInfo] | None
    writers: list[PersonShortInfo] | None


class FilmEsSchema(BaseModel):
    id: str
    imdb_rating: float | None
    title: str
    description: str
    director: list[str] | None
    genre: list[str] | None
    actors: list[PersonShortInfo] | None
    writers: list[PersonShortInfo] | None


class GenreScheme(BaseModel):
    """Модель для валидации данных жанра от api"""
    uuid: UUID
    name: str
