from uuid import UUID

import numpy as np


class LSHIndex:
    def __init__(self, dim: int, num_tables: int = 5, num_hashes: int = 10):
        self.dim = dim
        self.num_tables = num_tables
        self.num_hashes = num_hashes
        self.tables: list[dict[str, list[UUID]]] = [{} for _ in range(num_tables)]
        self.hyperplanes: list[np.ndarray] = [
            np.random.randn(num_hashes, dim) for _ in range(num_tables)
        ]
        self.vectors: dict[UUID, np.ndarray] = {}

    def _hash(self, vector: np.ndarray, planes: np.ndarray) -> str:
        bits = vector.dot(planes.T) > 0
        return "".join(["1" if b else "0" for b in bits])

    def add(self, vector_id: UUID, vector: list[float]) -> None:
        vec_np = np.array(vector)
        self.vectors[vector_id] = vec_np
        for table, planes in zip(self.tables, self.hyperplanes, strict=False):
            key = self._hash(vec_np, planes)
            table.setdefault(key, []).append(vector_id)

    def search(self, query_vector: list[float], k: int = 3) -> list[tuple[UUID, float]]:
        query_np = np.array(query_vector)
        candidates = set()
        for table, planes in zip(self.tables, self.hyperplanes, strict=False):
            key = self._hash(query_np, planes)
            candidates.update(table.get(key, []))

        # Compute cosine similarity with candidates
        def cosine_sim(a, b):
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        scored = [
            (vector_id, cosine_sim(query_np, self.vectors[vector_id]))
            for vector_id in candidates
        ]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]
