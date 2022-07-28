from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from uuid import UUID

from services.film import FilmService, get_film_service
from services.genre import GenreService, get_genre_service
from models.models import PersonShortInfo
from core.config import api_settings
from core.localization import localization

router = APIRouter()

lang = api_settings.language


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


async def sort_checker(sort):
    if sort is not None:
        # Проверяем, валидно ли поле для сортировки
        if sort not in ('imdb_rating', '-imdb_rating'):
            raise ValueError(localization['wrong_sorting_field'][lang])
        # если первый символ в параметре сортировки это '-'
        if sort.find('-') == 0:
            # то приводим к нужному для ES формату
            sort = sort.strip('-') + ":desc"
    return sort


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
        sort: str = None,
        filter_genre: str | None = Query(default=None, alias="filter[genre]"),
        page: int = 1,
        page_size: int = api_settings.page_size,
        film_service: FilmService = Depends(get_film_service),
        genre_service: GenreService = Depends(get_genre_service)
) -> list[Film] | None:
    # Пробуем получить имя жанра, указанное в запросе
    if filter_genre:
        filter_genre = await get_genre_name(genre_service, filter_genre)

    # Проверяем параметр 'sort'
    checked_sort = await sort_checker(sort)

    # Получаем фильмы
    films = await film_service.get_films(
        page=page,
        page_size=page_size,
        sort=checked_sort,
        filter_genre=filter_genre
    )
    if not films:
        # Если фильмы не найдены, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['films_not_found'][lang])

    film_list = []
    for film in films:
        film_list.append(
            Film(
                uuid=film.id,
                title=film.title,
                imdb_rating=film.imdb_rating,
                description=film.description,
                directors=film.director,
                genre=film.genre,
                actors=film.actors,
                writers=film.writers,
            )
        )

    return film_list


@router.get(
    '/search',
    response_model=list[Film],
    summary="Search films",
    description="Search films by provided query"
)
async def search_films(
        query: str = None,
        page: int = 1,
        page_size: int = api_settings.page_size,
        film_service: FilmService = Depends(get_film_service),
) -> Film:
    """Осуществляет поиск фильмов по базе и возвращает список с подходящими фильмами,
    учитывая пагинацию"""
    films = await film_service.get_films(
        query=query,
        page=page,
        page_size=page_size,
    )
    if not films:
        # Если фильмы не найдены, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['films_not_found'][lang])

    result = []

    for film in films:
        result.append(
            Film(
                uuid=film.id,
                title=film.title,
                imdb_rating=film.imdb_rating,
                description=film.description,
                directors=film.director,
                genre=film.genre,
                actors=film.actors,
                writers=film.writers,
            )
        )

    return result


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
    return Film(
        uuid=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        directors=film.director,
        genre=film.genre,
        actors=film.actors,
        writers=film.writers,
    )
