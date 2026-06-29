from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

client = QdrantClient(
    url="https://e5e68a2a-6fe0-4523-a56d-21705ad8bb0d.us-west-1-0.aws.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MWE2ZTFjYmQtZjA5YS00NzAwLWEzYWItYTAwMjcyZjBkMGRiIn0.t0kmgv27BsebU-Y9UTyihJDXADwBczJwUX0LSUHgbLE",
)

collection_name = "reflective_case_memory"

# Check if the collection already exists
collections = client.get_collections().collections
existing = [c.name for c in collections]

if collection_name not in existing:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        ),
    )
    print(f"✅ Collection '{collection_name}' created successfully!")
else:
    print(f"ℹ️ Collection '{collection_name}' already exists.")