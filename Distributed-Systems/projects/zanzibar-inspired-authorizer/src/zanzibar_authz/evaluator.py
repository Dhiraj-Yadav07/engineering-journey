from .store import TupleStore


class CheckEngine:
    def __init__(self, store: TupleStore) -> None:
        self._store = store

    def check(
        self,
        subject_type: str,
        subject_id: str,
        object_type: str,
        object_id: str,
        relation: str,
        visited: set[tuple[str, str, str, str, str]] | None = None,
        depth: int = 0,
    ) -> bool:
        if visited is None:
            visited = set()

        # Prevent unbounded recursion.
        if depth > 10:
            return False

        check_key = (
            subject_type,
            subject_id,
            object_type,
            object_id,
            relation,
        )

        # Prevent cycles in the relationship graph.
        if check_key in visited:
            return False

        visited.add(check_key)

        tuples = self._store.find(
            object_type,
            object_id,
            relation,
        )

        for tuple_record in tuples:
            # Case 1:
            # Direct relationship to a concrete user.
            if (
                tuple_record.subject_type == subject_type
                and tuple_record.subject_id == subject_id
                and tuple_record.subject_relation is None
            ):
                return True

            # Case 2:
            # Relationship points to a userset.
            if tuple_record.subject_relation is not None:
                if (
                    tuple_record.subject_type == "group"
                    and tuple_record.subject_id
                    and tuple_record.subject_relation == "member"
                ):
                    if self.check(
                        subject_type=subject_type,
                        subject_id=subject_id,
                        object_type="group",
                        object_id=tuple_record.subject_id,
                        relation=tuple_record.subject_relation,
                        visited=visited,
                        depth=depth + 1,
                    ):
                        return True

        return False