import logging
from typing import Any
from uuid import UUID

import numpy as np

from vector_store.app.db.index import Index

logger = logging.getLogger(__name__)

class LSHIndex(Index):
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
        vec_np = vec_np / np.linalg.norm(vec_np)  # Normalize the vector
        self.vectors[vector_id] = vec_np
        for i, table in enumerate(self.tables):
            planes = self.hyperplanes[i]
            key = self._hash(vec_np, planes)
            table.setdefault(key, []).append(vector_id)

    def remove(self, vector_id: UUID) -> None:
        self.vectors.pop(vector_id, None)
        for table in self.tables:
            keys_to_remove = [k for k, ids in table.items() if vector_id in ids]
            for k in keys_to_remove:
                table[k].remove(vector_id)
                if not table[k]:
                    del table[k]

    def search(self, query_vector: list[float], k: int = 3) -> list[tuple[UUID, float]]:
        query_np = np.array(query_vector)
        query_np = query_np / np.linalg.norm(query_np)  # Normalize the query vector
        candidates = set()
        for i, table in enumerate(self.tables):
            planes = self.hyperplanes[i]
            key = self._hash(query_np, planes)
            candidates.update(table.get(key, []))

        # If no candidates, return empty
        if not candidates:
            logger.info("No candidates in lsh, using brute force search instead")
            return []

        def cosine_sim(a, b):
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        scored = [
            (vector_id, cosine_sim(query_np, self.vectors[vector_id]))
            for vector_id in candidates
        ]
        scored.sort(key=lambda x: -x[1])

        return scored[:k]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dim": self.dim,
            "num_tables": self.num_tables,
            "num_hashes": self.num_hashes,
            "tables": [
                {k: [str(uid) for uid in v] for k, v in table.items()}
                for table in self.tables
            ],
            "hyperplanes": [plane.tolist() for plane in self.hyperplanes],
            "vectors": {str(uid): vec.tolist() for uid, vec in self.vectors.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LSHIndex":
        index = cls(
            dim=data["dim"],
            num_tables=data["num_tables"],
            num_hashes=data["num_hashes"],
        )
        index.tables = [
            {k: [UUID(uid) for uid in v] for k, v in table.items()}
            for table in data["tables"]
        ]
        index.hyperplanes = [np.array(plane) for plane in data["hyperplanes"]]
        index.vectors = {
            UUID(uid): np.array(vec) for uid, vec in data["vectors"].items()
        }
        return index
