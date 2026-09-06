from dataclasses import dataclass


@dataclass(frozen=True)
class Direct:
    relation: str


@dataclass(frozen=True)
class Union:
    expressions: tuple[object, ...]


@dataclass(frozen=True)
class Intersection:
    expressions: tuple[object, ...]


@dataclass(frozen=True)
class Exclusion:
    base: object
    excluded: object