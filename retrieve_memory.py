from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

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
# New "incoming report" or query
# -----------------------------
query_text = "The client is currently homeless and struggling to find stable accommodation"

# -----------------------------
# Create embedding
# -----------------------------
query_vector = model.encode(query_text).tolist()

# -----------------------------
# Search Qdrant
# -----------------------------
search_results = client.query_points(
    collection_name="reflective_case_memory",
    query=query_vector,
    limit=3,
    with_payload=True
).points


# -----------------------------
# Display results
# -----------------------------
print("\n🔍 Retrieved Case Memory:\n")

for i, result in enumerate(search_results):
    print(f"Result {i+1}")
    print("Score:", result.score)
    print("Client:", result.payload["client_name"])
    print("Type:", result.payload["document_type"])
    print("Text:", result.payload["report_text"])
    print("-" * 50)