from dataclasses import dataclass

from .expressions import Direct, Exclusion, Intersection, Union


@dataclass(frozen=True)
class RelationRule:
    """
    Defines how a relation is evaluated.

    Example:

        viewer = owner UNION editor UNION direct_viewer
    """

    relation: str
    expression: object | None = None

    def __post_init__(self) -> None:
        if self.expression is None:
            object.__setattr__(self, "expression", Direct(self.relation))


@dataclass
class Namespace:
    """
    Defines the relationships supported by one object type.
    """

    name: str
    relations: dict[str, RelationRule]

    def get_relation(self, relation: str) -> RelationRule:
        try:
            return self.relations[relation]
        except KeyError as exc:
            raise ValueError(
                f"Relation '{relation}' is not defined "
                f"for namespace '{self.name}'"
            ) from exc