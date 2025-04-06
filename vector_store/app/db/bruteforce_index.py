import heapq
from uuid import UUID

import numpy as np

from vector_store.app.db.index import Index


class BruteForceIndex(Index):
    def __init__(self, metric: str = "euclidean"):
        self.vectors: list[tuple[UUID, np.ndarray]] = []
        self.metric = metric

    def add(self, vector_id: UUID, vector: list[float]) -> None:
        self.vectors.append((vector_id, np.array(vector)))

    def remove(self, vector_id: UUID) -> None:
        self.vectors = [(i, v) for (i, v) in self.vectors if i != vector_id]

    def _distance(self, a: np.ndarray, b: np.ndarray) -> float:
        if self.metric == "euclidean":
            return np.linalg.norm(a - b)
        elif self.metric == "cosine":
            if not np.any(a) or not np.any(b):
                return 1.0
            return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def search(self, query_vector: list[float], k: int) -> list[tuple[UUID, float]]:
        query_vector = np.array(query_vector)
        results = []

        for vector_id, vec in self.vectors:
            dist = self._distance(query_vector, vec)
            if len(results) < k:
                heapq.heappush(results, (-dist, vector_id))
            else:
                if dist < -results[0][0]:
                    heapq.heappushpop(results, (-dist, vector_id))

        return sorted(
            [(vector_id, -d) for (d, vector_id) in results], key=lambda x: x[1]
        )
