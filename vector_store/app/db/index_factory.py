from vector_store.app.db.bruteforce_index import BruteForceIndex
from vector_store.app.db.index import Index
from vector_store.app.db.lsh_index import LSHIndex


class IndexFactory:
    @staticmethod
    def create(index_type: str = "lsh", **kwargs) -> Index:
        if index_type == "lsh":
            dim = kwargs.get("dim", 1024) # Delete
            return LSHIndex(dim=dim)
        elif index_type == "bruteforce":
            metric = kwargs.get("metric", "euclidean")
            return BruteForceIndex(metric=metric)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
