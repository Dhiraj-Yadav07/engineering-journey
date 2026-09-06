from .expressions import (
    Direct,
    Exclusion,
    Intersection,
    TupleToUserset,
    Union,
)
from .models import ConsistencyToken
from .namespace import Namespace
from .store import TupleStore


class CheckEngine:
    MAX_DEPTH = 10

    def __init__(
        self,
        store: TupleStore,
        namespaces: dict[str, Namespace],
    ) -> None:
        self._store = store
        self._namespaces = namespaces

    def check(
        self,
        subject_type: str,
        subject_id: str,
        object_type: str,
        object_id: str,
        relation: str,
        consistency_token: ConsistencyToken | None = None,
        visited: set[tuple[str, str, str, str, str]] | None = None,
        depth: int = 0,
    ) -> bool:
        """
        Public authorization API.

        Callers provide a ConsistencyToken. The evaluator converts
        it to an internal snapshot version and evaluates the entire
        authorization graph against that snapshot.
        """
        snapshot_version = (
            consistency_token.snapshot_version
            if consistency_token is not None
            else None
        )

        return self._check_at_snapshot(
            subject_type=subject_type,
            subject_id=subject_id,
            object_type=object_type,
            object_id=object_id,
            relation=relation,
            snapshot_version=snapshot_version,
            visited=visited,
            depth=depth,
        )

    def _check_at_snapshot(
        self,
        subject_type: str,
        subject_id: str,
        object_type: str,
        object_id: str,
        relation: str,
        snapshot_version: int | None,
        visited: set[tuple[str, str, str, str, str]] | None = None,
        depth: int = 0,
    ) -> bool:
        """
        Internal recursive authorization check.

        Internal evaluator code passes snapshot_version directly so
        the same consistency context is preserved throughout recursion.
        """
        if visited is None:
            visited = set()

        if depth > self.MAX_DEPTH:
            return False

        check_key = (
            subject_type,
            subject_id,
            object_type,
            object_id,
            relation,
        )

        if check_key in visited:
            return False

        visited.add(check_key)

        namespace = self._namespaces.get(object_type)

        if namespace is None:
            return False

        rule = namespace.get_relation(relation)

        return self._evaluate_expression(
            expression=rule.expression,
            subject_type=subject_type,
            subject_id=subject_id,
            object_type=object_type,
            object_id=object_id,
            snapshot_version=snapshot_version,
            visited=visited,
            depth=depth,
        )

    def _evaluate_expression(
        self,
        expression: object,
        subject_type: str,
        subject_id: str,
        object_type: str,
        object_id: str,
        snapshot_version: int | None,
        visited: set[tuple[str, str, str, str, str]],
        depth: int,
    ) -> bool:

        if isinstance(expression, Direct):
            return self._evaluate_direct_relation(
                relation=expression.relation,
                subject_type=subject_type,
                subject_id=subject_id,
                object_type=object_type,
                object_id=object_id,
                snapshot_version=snapshot_version,
                visited=visited,
                depth=depth,
            )

        if isinstance(expression, TupleToUserset):
            return self._evaluate_tuple_to_userset(
                expression=expression,
                subject_type=subject_type,
                subject_id=subject_id,
                object_type=object_type,
                object_id=object_id,
                snapshot_version=snapshot_version,
                visited=visited,
                depth=depth,
            )

        if isinstance(expression, Union):
            return any(
                self._evaluate_expression(
                    expression=child,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    object_type=object_type,
                    object_id=object_id,
                    snapshot_version=snapshot_version,
                    visited=visited.copy(),
                    depth=depth + 1,
                )
                for child in expression.expressions
            )

        if isinstance(expression, Intersection):
            return all(
                self._evaluate_expression(
                    expression=child,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    object_type=object_type,
                    object_id=object_id,
                    snapshot_version=snapshot_version,
                    visited=visited.copy(),
                    depth=depth + 1,
                )
                for child in expression.expressions
            )

        if isinstance(expression, Exclusion):
            allowed = self._evaluate_expression(
                expression=expression.base,
                subject_type=subject_type,
                subject_id=subject_id,
                object_type=object_type,
                object_id=object_id,
                snapshot_version=snapshot_version,
                visited=visited.copy(),
                depth=depth + 1,
            )

            if not allowed:
                return False

            excluded = self._evaluate_expression(
                expression=expression.excluded,
                subject_type=subject_type,
                subject_id=subject_id,
                object_type=object_type,
                object_id=object_id,
                snapshot_version=snapshot_version,
                visited=visited.copy(),
                depth=depth + 1,
            )

            return not excluded

        raise TypeError(
            f"Unsupported userset expression: "
            f"{type(expression).__name__}"
        )

    def _evaluate_direct_relation(
        self,
        relation: str,
        subject_type: str,
        subject_id: str,
        object_type: str,
        object_id: str,
        snapshot_version: int | None,
        visited: set[tuple[str, str, str, str, str]],
        depth: int,
    ) -> bool:
        tuples = self._store.find(
            object_type,
            object_id,
            relation,
            snapshot_version=snapshot_version,
        )

        for tuple_record in tuples:

            # Direct user relationship:
            #
            # document:design#direct_viewer@user:alice
            #
            if (
                tuple_record.subject_type == subject_type
                and tuple_record.subject_id == subject_id
                and tuple_record.subject_relation is None
            ):
                return True

            # Userset relationship:
            #
            # document:design#direct_viewer
            #     @group:engineering#member
            #
            if tuple_record.subject_relation is not None:
                if self._check_at_snapshot(
                    subject_type=subject_type,
                    subject_id=subject_id,
                    object_type=tuple_record.subject_type,
                    object_id=tuple_record.subject_id,
                    relation=tuple_record.subject_relation,
                    snapshot_version=snapshot_version,
                    visited=visited.copy(),
                    depth=depth + 1,
                ):
                    return True

        return False

    def _evaluate_tuple_to_userset(
        self,
        expression: TupleToUserset,
        subject_type: str,
        subject_id: str,
        object_type: str,
        object_id: str,
        snapshot_version: int | None,
        visited: set[tuple[str, str, str, str, str]],
        depth: int,
    ) -> bool:
        tuples = self._store.find(
            object_type,
            object_id,
            expression.tupleset_relation,
            snapshot_version=snapshot_version,
        )

        for tuple_record in tuples:
            # Tuple-to-userset can point directly to another object:
            #
            # document:design#parent@folder:engineering-docs
            #
            # It can also point to a userset:
            #
            # document:design#viewer@group:engineering#member
            #
            # In both cases, evaluate the computed relation on
            # the referenced object.
            if self._check_at_snapshot(
                subject_type=subject_type,
                subject_id=subject_id,
                object_type=tuple_record.subject_type,
                object_id=tuple_record.subject_id,
                relation=expression.computed_userset_relation,
                snapshot_version=snapshot_version,
                visited=visited.copy(),
                depth=depth + 1,
            ):
                return True

        return False