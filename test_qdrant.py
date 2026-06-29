from qdrant_client import QdrantClient

client = QdrantClient(":memory:")

collections = client.get_collections()

print(collections)