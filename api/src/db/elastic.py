from typing import Optional
from elasticsearch import AsyncElasticsearch

MOVIES_ES_INDEX = 'movies'
GENRES_ES_INDEX = 'genres'

es: Optional[AsyncElasticsearch] = None

# Функция понадобится при внедрении зависимостей
async def get_elastic() -> AsyncElasticsearch:
    return es