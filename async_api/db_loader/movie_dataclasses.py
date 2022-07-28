import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FilmWork:
    title: str
    description: str
    creation_date: str
    file_path: str
    type: str
    created_at: str
    updated_at: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    rating: float = field(default=0.0)


@dataclass(frozen=True)
class Person:
    full_name: str
    created_at: str
    updated_at: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class Genre:
    name: str
    description: str
    created_at: str
    updated_at: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class PersonFilmWork:
    role: str
    created_at: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    person_id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class GenreFilmWork:
    created_at: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    genre_id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
