from cachetools import LRUCache

from vector_store.app.constants import CHUNKS_LRU_CACHE_SIZE, LSH_LRU_CACHE_SIZE

chunk_cache = LRUCache(maxsize=CHUNKS_LRU_CACHE_SIZE)
index_cache = LRUCache(maxsize=LSH_LRU_CACHE_SIZE)  # LSH Index
