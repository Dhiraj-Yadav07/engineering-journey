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


@dataclass(frozen=True)
class TupleToUserset:
    """
    Follow a relation to another object, then evaluate
    a relation on that referenced object.

    Example:

        document#parent -> folder#viewer
    """

    tupleset_relation: str
    computed_userset_relation: str