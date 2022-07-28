import orjson

from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class MainModel(BaseModel):
    id: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Person(MainModel):
    full_name: str
    films_ids: list[str]
    role: str


class PersonShortInfo(MainModel):
    name: str


class Film(MainModel):
    imdb_rating: float | None
    title: str
    description: str
    director: list[str] | None
    genre: list[str] | None
    actors: list[PersonShortInfo] | None
    writers: list[PersonShortInfo] | None


class Genre(MainModel):
    name: str
