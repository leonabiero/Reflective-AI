import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# -----------------------------
# Connect to Qdrant
# -----------------------------
client = QdrantClient(
    url="https://e5e68a2a-6fe0-4523-a56d-21705ad8bb0d.us-west-1-0.aws.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MWE2ZTFjYmQtZjA5YS00NzAwLWEzYWItYTAwMjcyZjBkMGRiIn0.t0kmgv27BsebU-Y9UTyihJDXADwBczJwUX0LSUHgbLE",
)

# -----------------------------
# Load embedding model
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# Sample report
# -----------------------------
report = """
The client reports recently losing temporary accommodation following the end
of a short-term rental agreement.

The client arrived on time, appeared calm, and explained that they have been
sleeping intermittently with friends while seeking more stable housing.

The client expressed a strong desire to obtain employment and identified
previous experience in hospitality.
"""

# -----------------------------
# Create embedding
# -----------------------------
embedding = model.encode(report).tolist()

# -----------------------------
# Metadata
# -----------------------------
payload = {
    "client_id": "C001",
    "client_name": "John Mwangi",
    "case_id": str(uuid.uuid4()),
    "document_type": "Intake Assessment",
    "date": "2026-06-28",
    "author": "Worker 01",
    "service": "Social Accommodation",
    "language": "English",
    "report_text": report
}

# -----------------------------
# Upload to Qdrant
# -----------------------------
client.upsert(
    collection_name="reflective_case_memory",
    points=[
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload
        )
    ]
)

print("✅ First document stored successfully!")