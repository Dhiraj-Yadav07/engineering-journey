from dataclasses import dataclass

@dataclass(frozen=True)
class ConsistencyToken:
    snapshot_version: int

@dataclass(frozen=True)
class TupleRecord:
    object_type: str
    object_id: str
    relation: str
    subject_type: str
    subject_id: str
    subject_relation: str | None = None

    # Version at which this tuple became active.
    valid_from: int = 0

    # Version at which this tuple stopped being active.
    # None means the tuple is still active.
    valid_to: int | None = None

    @property
    def object_ref(self) -> str:
        return f"{self.object_type}:{self.object_id}"

    @property
    def subject_ref(self) -> str:
        if self.subject_relation:
            return (
                f"{self.subject_type}:{self.subject_id}"
                f"#{self.subject_relation}"
            )

        return f"{self.subject_type}:{self.subject_id}"

    def is_visible_at(self, snapshot_version: int) -> bool:
        return (
            self.valid_from <= snapshot_version
            and (
                self.valid_to is None
                or snapshot_version < self.valid_to
            )
        )