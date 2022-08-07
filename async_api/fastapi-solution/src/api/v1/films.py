from enum import Enum
from http import HTTPStatus
from uuid import UUID

from api.v1.paginator import Paginator
from core.config import api_settings
from core.localization import localization
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from services.film import FilmService, get_film_service
from services.genre import GenreService, get_genre_service

router = APIRouter()

lang = api_settings.language


class PersonShortInfo(BaseModel):
    id: str
    name: str


class Film(BaseModel):
    """Полный набор полей для эндпоинта с описанием одного фильма"""
    uuid: UUID
    title: str
    imdb_rating: float
    genre: list[str] | None
    description: str | None
    directors: list[str] | None
    actors: list[PersonShortInfo] | None
    writers: list[PersonShortInfo] | None


class SortDirection(Enum):
    asc = 'imdb_rating'
    desc = '-imdb_rating'

    def get_es_sort(self):
        return f'{self.value.strip("-")}:{self.name}'


async def get_genre_name(genre_service, genre_uuid) -> str | None:
    '''Возвращает имя жанра по uuid либо None'''
    genre = await genre_service.get_by_id(genre_uuid)
    if genre:
        return genre.name
    return None


@router.get(
    '/',
    response_model=list[Film],
    summary="Get films",
    description="Get films with all information",
)
async def filter_films(
        sort: SortDirection | None = None,
        filter_genre: str | None = Query(default=None, alias="filter[genre]"),
        paginator: Paginator = Depends(),
        film_service: FilmService = Depends(get_film_service),
        genre_service: GenreService = Depends(get_genre_service)
) -> list[Film] | None:
    # Пробуем получить имя жанра, указанное в запросе
    if filter_genre:
        filter_genre = await get_genre_name(genre_service, filter_genre)

    checked_sort = sort.get_es_sort() if sort else None

    # Получаем фильмы
    films = await film_service.get_films(
        page=paginator.page_number,
        page_size=paginator.page_size,
        sort=checked_sort,
        filter_genre=filter_genre
    )
    if not films:
        # Если фильмы не найдены, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['films_not_found'][lang])

    return [Film(uuid=film.id, directors=film.director, **film.dict()) for film in films]


@router.get(
    '/search',
    response_model=list[Film],
    summary="Search films",
    description="Search films by provided query"
)
async def search_films(
        query: str = None,
        paginator: Paginator = Depends(),
        film_service: FilmService = Depends(get_film_service),
) -> list[Film]:
    """Осуществляет поиск фильмов по базе и возвращает список с подходящими фильмами,
    учитывая пагинацию"""
    films = await film_service.get_films(
        query=query,
        page=paginator.page_number,
        page_size=paginator.page_size,
    )
    if not films:
        # Если фильмы не найдены, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['films_not_found'][lang])

    return [Film(uuid=film.id, directors=film.director, **film.dict()) for film in films]


@router.get(
    '/{film_id}',
    response_model=Film,
    summary="Get film by id",
    description="Get full film info by provided ID"
)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['films_not_found'][lang])

    # Перекладываем данные из models.Film в Film
    return Film(uuid=film.id, directors=film.director, **film.dict())
