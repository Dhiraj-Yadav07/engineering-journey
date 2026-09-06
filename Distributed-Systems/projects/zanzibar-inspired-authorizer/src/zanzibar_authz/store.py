from .models import TupleRecord


class TupleStore:
    def __init__(self) -> None:
        self._tuples: list[TupleRecord] = []

    def add(self, tuple_record: TupleRecord) -> None:
        if tuple_record not in self._tuples:
            self._tuples.append(tuple_record)

    def find(
        self,
        object_type: str,
        object_id: str,
        relation: str,
    ) -> list[TupleRecord]:
        return [
            tuple_record
            for tuple_record in self._tuples
            if (
                tuple_record.object_type == object_type
                and tuple_record.object_id == object_id
                and tuple_record.relation == relation
            )
        ]