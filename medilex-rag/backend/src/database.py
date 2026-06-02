# backend/src/database.py mein ye replace karein
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

def init_db():
    collection_name = "medilex_encyclopedia"
    
    # Purana galat collection delete karein
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config={
            "default": models.VectorParams(size=1024, distance=models.Distance.COSINE),
        },
        sparse_vectors_config={
            "keywords": models.SparseVectorParams()
        }
    )
    print(f"✅ Collection {collection_name} created with 'default' vector name.")

if __name__ == "__main__":
    init_db()