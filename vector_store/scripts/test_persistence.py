from datetime import datetime, timezone
from uuid import uuid4

from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.db.persistence import load_data, load_lsh, save_data, save_indices
from vector_store.app.models.library import Library

# Create dummy data
lib_id = uuid4()
library = Library(
    id=lib_id,
    name="Test Library",
    description="Just testing",
    created_at=datetime.now(timezone.utc),
    index_type="lsh",
)

# Save library
save_data({lib_id: library}, {}, {})

# Save dummy LSH index
index = LSHIndex(dim=EMBEDDING_DIM)
index.add(uuid4(), [0.1] * EMBEDDING_DIM)
save_indices({lib_id: index})

# Load and print
libs, docs, chks = load_data()
indices = load_lsh()

print("✅ Libraries:", libs)
print("✅ Indices:", indices)
