import numpy as np
import heapq

class BruteForceIndex:
    def __init__(self, metric: str = 'euclidean'):
        self.vectors = []  # List of (id, vector)
        self.metric = metric

    def add(self, id, vector):
        self.vectors.append((id, np.array(vector)))

    def remove(self, id):
        self.vectors = [(i, v) for (i, v) in self.vectors if i != id]

    def _distance(self, a, b):
        if self.metric == 'euclidean':
            return np.linalg.norm(a - b)
        elif self.metric == 'cosine':
            if not np.any(a) or not np.any(b):
                return 1.0
            return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def search(self, query_vector, k):
        query_vector = np.array(query_vector)
        results = []

        for id, vec in self.vectors:
            dist = self._distance(query_vector, vec)
            if len(results) < k:
                heapq.heappush(results, (-dist, id))  # max-heap
            else:
                if dist < -results[0][0]:
                    heapq.heappushpop(results, (-dist, id))

        return sorted([(id, -d) for (d, id) in results], key=lambda x: x[1])
