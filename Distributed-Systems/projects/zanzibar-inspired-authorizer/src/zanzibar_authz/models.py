from dataclasses import dataclass


@dataclass(frozen=True)
class TupleRecord:
    object_type: str
    object_id: str
    relation: str
    subject_type: str
    subject_id: str
    subject_relation: str | None = None

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