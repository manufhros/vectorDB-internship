from abc import ABC, abstractmethod
from uuid import UUID


class Index(ABC):
    @abstractmethod
    def add(self, vector_id: UUID, vector: list[float]) -> None:
        pass

    @abstractmethod
    def remove(self, vector_id: UUID) -> None:
        pass

    @abstractmethod
    def search(self, query_vector: list[float], k: int) -> list[tuple[UUID, float]]:
        pass
