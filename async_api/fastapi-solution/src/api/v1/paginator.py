from fastapi import Query

from core.config import api_settings


class Paginator:
    def __init__(
            self,
            page_size: int = Query(
                default=api_settings.page_size, alias='page[size]',
                description='Items amount on page', ge=1, le=500
            ),
            page_number: int = Query(default=1, alias='page[number]', description='Page number for pagination', ge=1),
    ):
        self.page_size = page_size
        self.page_number = page_number
