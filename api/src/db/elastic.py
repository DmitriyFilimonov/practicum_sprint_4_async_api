from typing import Optional
from elasticsearch import AsyncElasticsearch

MOVIES_ES_INDEX = 'movies'
GENRES_ES_INDEX = 'genres'
PERSONS_ES_INDEX = 'persons'

es: Optional[AsyncElasticsearch] = None

# Функция понадобится при внедрении зависимостей
async def get_elastic() -> AsyncElasticsearch:
    return es