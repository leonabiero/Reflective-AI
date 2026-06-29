from qdrant_client import QdrantClient
from qdrant_client.http import models

QDRANT_URL = "https://e5e68a2a-6fe0-4523-a56d-21705ad8bb0d.us-west-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MWE2ZTFjYmQtZjA5YS00NzAwLWEzYWItYTAwMjcyZjBkMGRiIn0.t0kmgv27BsebU-Y9UTyihJDXADwBczJwUX0LSUHgbLE"

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Index for fast filtering by client_id
client.create_payload_index(
    collection_name="reflective_case_memory",
    field_name="client_id",
    field_schema=models.PayloadSchemaType.KEYWORD
)

# NEW: Index for smart name-based matching
client.create_payload_index(
    collection_name="reflective_case_memory",
    field_name="client_name",
    field_schema=models.PayloadSchemaType.KEYWORD
)

print("✅ Indexes for client_id and client_name created successfully")