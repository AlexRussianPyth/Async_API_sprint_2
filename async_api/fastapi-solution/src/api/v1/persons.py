from http import HTTPStatus
from uuid import UUID

from api.v1.films import Film
from api.v1.paginator import Paginator
from core.config import api_settings
from core.localization import localization
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.film import FilmService, get_film_service
from services.person import PersonService, get_person_service

router = APIRouter()

lang = api_settings.language


class Person(BaseModel):
    """Полный набор полей для эндпоинта с описанием одного человека"""
    uuid: UUID
    full_name: str
    role: str
    film_ids: list[str]


@router.get(
    '/search',
    response_model=list[Person],
    summary="Search for persons",
    description="Get info about persons which names similar to provided query"
)
async def search_persons(
        query: str = None,
        paginator: Paginator = Depends(),
        person_service: PersonService = Depends(get_person_service)
        ) -> list[Person]:
    """Осуществляет поиск людей по базе и возвращает список с подходящими людьми,
    учитывая пагинацию"""
    persons = await person_service.search_persons(query, paginator.page_number, paginator.page_size)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['persons_not_found'][lang])

    result = []

    for person in persons:
        result.append(Person(
            uuid=person.id,
            full_name=person.full_name,
            role=person.role,
            film_ids=person.films_ids
        ))

    return result


@router.get(
    '/{person_id}',
    response_model=Person,
    summary="Get person by id",
    description="Get person info by provided id"
)
async def person_details(person_id: str, person_service: PersonService = Depends(get_person_service)) -> Person:
    """Возвращает Человека по id, либо HTTPException, если Человека с таким id не существует"""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['person_not_found'][lang])

    return Person(
        uuid=UUID(person.id),
        full_name=person.full_name,
        role=person.role,
        film_ids=person.films_ids
    )


@router.get(
    '/{person_id}/film',
    response_model=list[Film],
    summary="Get films by person",
    description="Show information about films in which participated provided Person"
)
async def films_by_person(
        person_id: str,
        person_service: PersonService = Depends(get_person_service),
        film_service: FilmService = Depends(get_film_service)
) -> list[Film]:
    """Возвращает список фильмов, в которых участвовал Человек с данным id, либо HTTPException, если человека
    или фильмов не существует"""
    # Проверяем, что Человек с данным id существует
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['person_not_found'][lang])

    # Получаем список фильмов, в которых принимал участие данный Человек
    films = await person_service.films_by_person(person_name=person.full_name)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['film_for_person_not_found'][lang])

    result = []

    for film_id in films:
        film = await film_service.get_by_id(film_id)

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
