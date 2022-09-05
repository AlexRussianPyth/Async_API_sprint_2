from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.config import api_settings
from core.localization import localization
from services.auth import JWTBearer
from services.genre import GenreService, get_genre_service

router = APIRouter()

lang = api_settings.language


class Genre(BaseModel):
    """Pydantic модель для эндпоинта с описанием жанра"""
    uuid: UUID
    name: str


@router.get(
    '/',
    response_model=list[Genre],
    summary="Get genres",
    description="Get list of genres by query or just full list of all genres in database"
)
async def genre_list(
        page: int = 1,
        genre_service: GenreService = Depends(get_genre_service),
        query: str = None,
        user: str = Depends(JWTBearer()),
        ) -> list[Genre]:
    genres = await genre_service.get_genres(page=page, query=query)
    if not genres:
        # Если список жанров не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['genres_not_found'][lang])

    return [Genre(uuid=genre.id, name=genre.name) for genre in genres]


@router.get(
    '/{genre_uuid}',
    response_model=Genre,
    summary="Get genre",
    description="Get info about genre by provided id"
)
async def genre_details(
        genre_uuid: str,
        genre_service: GenreService = Depends(get_genre_service),
        user: str = Depends(JWTBearer()),
) -> Genre:
    genre = await genre_service.get_by_id(genre_uuid)
    if not genre:
        # Если жанр не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=localization['genre_not_found'][lang])

    return Genre(uuid=genre.id, name=genre.name)
