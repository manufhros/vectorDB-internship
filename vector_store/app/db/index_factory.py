from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.bruteforce_index import BruteForceIndex
from vector_store.app.db.index import Index
from vector_store.app.db.lsh_index import LSHIndex


class IndexFactory:
    @staticmethod
    def create(
        index_type: str = "lsh", dim: int = EMBEDDING_DIM, metric: str = "euclidean"
    ) -> Index:
        if index_type == "lsh":
            return LSHIndex(dim=dim)
        elif index_type == "bruteforce":
            return BruteForceIndex(metric=metric)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
