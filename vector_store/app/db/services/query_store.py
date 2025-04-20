import logging
import os
from uuid import UUID

import cohere
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.index_factory import IndexFactory
from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.db.repositories.chunk_repo import ChunkRepository
from vector_store.app.db.repositories.document_repo import DocumentRepository
from vector_store.app.db.repositories.library_repo import LibraryRepository
from vector_store.app.db.repositories.lsh_index_repo import LSHIndexRepository
from vector_store.app.db.services.chunk_store import ChunkStoreService
from vector_store.app.models.query import QueryRequest, QueryResult

load_dotenv()
cohere_client = cohere.Client(os.environ["COHERE_API_KEY"])

logger = logging.getLogger(__name__)


class QueryStoreService:
    def __init__(self, db: Session):
        self.db = db
        self.library_repo = LibraryRepository(db)
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.lsh_repo = LSHIndexRepository(db)
        self.chunk_service = ChunkStoreService(self.db)

    # Query
    def query_chunks(self, library_id: UUID, query: QueryRequest) -> list[QueryResult]:
        # 1. Get the library or raise a 404 if it does not exist
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # 2. Get or build the index for the library
        index = self._get_or_build_index(library_id, library.index_type)

        # 3. Use the provided embedding or generate one from text
        embedding = query.embedding or self._generate_query_embedding(query)

        # 4. Validate that the embedding has the correct dimensionality
        if len(embedding) != EMBEDDING_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding must have dimension {EMBEDDING_DIM}, but got {len(embedding)}",
            )

        # 5. Perform the similarity search
        try:
            results = index.search(embedding, query.k)

            # 5a. If no results and using LSH, fallback to brute force
            if not results and isinstance(index, LSHIndex):
                logger.info(
                    "LSH search returned no results, falling back to brute force"
                )
                results = self._fallback_bruteforce(library_id, embedding, query.k)

        except ValueError as err:
            raise HTTPException(
                status_code=400, detail=f"Error during similarity search: {str(err)}"
            ) from err

        # 6. Build and return the final query result list
        return self._build_query_results(results)

    # Index management helper methods
    def _get_or_build_index(self, library_id: UUID, index_type: str):
        """Get existing index or build a new one from chunks"""
        # For LSH indices, try to get from repository first
        if index_type == "lsh":
            index = self.lsh_repo.get(library_id)
            if index:
                return index

        # Create a new index
        index = IndexFactory.create(index_type=index_type, dim=EMBEDDING_DIM)

        # Populate with all chunks for this library
        chunks = self.chunk_repo.list_by_library(library_id)
        for chunk in chunks:
            index.add(chunk.id, chunk.embedding)

        # Persist LSH indices
        if index_type == "lsh":
            self.lsh_repo.save(library_id, index)

        return index

    def _build_query_results(
        self, results: list[tuple[UUID, float]]
    ) -> list[QueryResult]:
        output = []
        for chunk_id, score in results:
            chunk = self.chunk_service.get_chunk(chunk_id)
            if not chunk:
                continue
            output.append(
                QueryResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    score=min(score, 1.0),
                    text=chunk.text,
                    meta=chunk.meta,
                )
            )
        return output

    def _fallback_bruteforce(
        self, library_id: UUID, embedding: list[float], k: int
    ) -> list[tuple[UUID, float]]:
        """Create a brute force index from all chunks in the library and search"""
        chunks = self.chunk_repo.list_by_library(library_id)
        brute = IndexFactory.create("bruteforce", dim=EMBEDDING_DIM)
        for chunk in chunks:
            brute.add(chunk.id, chunk.embedding)
        return brute.search(embedding, k)

    # Embedding helper methods
    def _generate_query_embedding(self, query: QueryRequest) -> list[float]:
        if not query.text:
            raise HTTPException(
                status_code=400,
                detail="Either 'embedding' or 'text' must be provided",
            )
        try:
            response = cohere_client.embed(
                texts=[query.text],
                input_type="search_query",
                model="embed-english-v3.0",
            )
            return response.embeddings[0]
        except Exception as err:
            logger.exception("Error generating embedding with Cohere")
            raise HTTPException(
                status_code=500, detail="Failed to generate embedding"
            ) from err
