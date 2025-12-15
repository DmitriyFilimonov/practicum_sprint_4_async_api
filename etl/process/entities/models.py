from dataclasses import dataclass, field
from typing import Optional
from zoneinfo import ZoneInfo
from datetime import datetime
from uuid import UUID, uuid4

from process.parse_db_date import parse_db_date


@dataclass
class FilmworkPerson:
    person_id: str
    person_name: str
    person_role: str
    modified: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if isinstance(self.modified, str):
            self.modified = parse_db_date(self.modified).replace(
                tzinfo=ZoneInfo("Etc/UTC")
            )


@dataclass
class FilmworkGenre:
    genre_name: str
    modified: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if isinstance(self.modified, str):
            self.modified = parse_db_date(self.modified).replace(
                tzinfo=ZoneInfo("Etc/UTC")
            )


@dataclass(kw_only=True)
class FilmWork:
    id: UUID = field(default_factory=uuid4)
    title: str
    description: str
    rating: float
    type: str
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    persons: list[FilmworkPerson]
    genres: list[FilmworkGenre]

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)

        if isinstance(self.created, str):
            self.created = parse_db_date(self.created).replace(
                tzinfo=ZoneInfo("Etc/UTC")
            )

        if isinstance(self.modified, str):
            self.modified = parse_db_date(self.modified).replace(
                tzinfo=ZoneInfo("Etc/UTC")
            )


@dataclass
class FilmWorkESDocPerson:
    id: str
    name: str


@dataclass
class FilmWorkESDoc:
    id: str
    imdb_rating: float
    genres: list[str]
    title: str
    description: str
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmWorkESDocPerson]
    actors: list[FilmWorkESDocPerson]
    writers: list[FilmWorkESDocPerson]


@dataclass
class FilmWorkESDocRaw(FilmWorkESDoc):
    modified: datetime


@dataclass
class GenreFilmwork:
    id: str
    name: str
    description: Optional[str]
    modified: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if isinstance(self.modified, str):
            self.modified = parse_db_date(self.modified).replace(
                tzinfo=ZoneInfo("Etc/UTC")
            )
