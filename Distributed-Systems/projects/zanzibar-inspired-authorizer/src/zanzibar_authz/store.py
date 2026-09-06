from .models import TupleRecord


class TupleStore:
    def __init__(self) -> None:
        self._tuples: list[TupleRecord] = []

    def add(self, tuple_record: TupleRecord) -> None:
        if tuple_record in self._tuples:
            return

        self._tuples.append(tuple_record)

    def find(
        self,
        object_type: str,
        object_id: str,
        relation: str,
        snapshot_version: int | None = None,
    ) -> list[TupleRecord]:
        matches = [
            tuple_record
            for tuple_record in self._tuples
            if (
                tuple_record.object_type == object_type
                and tuple_record.object_id == object_id
                and tuple_record.relation == relation
            )
        ]

        if snapshot_version is None:
            return matches

        return [
            tuple_record
            for tuple_record in matches
            if tuple_record.is_visible_at(snapshot_version)
        ]