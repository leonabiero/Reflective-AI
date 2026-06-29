from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://e5e68a2a-6fe0-4523-a56d-21705ad8bb0d.us-west-1-0.aws.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MWE2ZTFjYmQtZjA5YS00NzAwLWEzYWItYTAwMjcyZjBkMGRiIn0.t0kmgv27BsebU-Y9UTyihJDXADwBczJwUX0LSUHgbLE",
)

collections = client.get_collections()

print("✅ Connected successfully!")
print(collections)