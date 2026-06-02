import os
import fitz  # PyMuPDF
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Load Environment Variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Configuration
PDF_PATH = os.path.join(os.path.dirname(__file__), "../data/English- The_Gale_Encyclopedia_of_Medicine_5th_Ed_9_Vol_Set_2015.pdf")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "../assets/images")
os.makedirs(IMAGE_DIR, exist_ok=True)

COLLECTION_NAME = "medilex_encyclopedia"

# 3. Initialize Qdrant Client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# 4. Load BGE Model Locally
print("⏳ Loading BAAI/bge-large-en-v1.5 locally...")
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
print("✅ Model loaded successfully.")

def generate_point_id(text):
    """Generates a stable integer ID based on text hash."""
    return int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (10**15)

def get_unique_sparse_vector(text):
    """Fix for Error 422: Ensures indices are unique within a single chunk."""
    words = text.lower().split()
    sparse_data = {}
    
    for word in words:
        if len(word) > 3:  # Only index meaningful words
            idx = hash(word) % 10000
            # If multiple words hash to the same index, we sum their frequency
            sparse_data[idx] = sparse_data.get(idx, 0.0) + float(words.count(word))
            
    indices = list(sparse_data.keys())
    values = list(sparse_data.values())
    return indices, values

def run_ingestion():
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: PDF not found at {PDF_PATH}")
        return

    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"🚀 Starting ingestion of {total_pages} pages...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "]
    )

    for page_num in range(4556,total_pages):
        try:
            page = doc[page_num]
            text = page.get_text()
            
            # --- Image Extraction ---
            image_filename = None
            image_list = page.get_images(full=True)
            if image_list:
                try:
                    xref = image_list[0][0]
                    base_image = doc.extract_image(xref)
                    image_filename = f"page_{page_num+1}.png"
                    with open(os.path.join(IMAGE_DIR, image_filename), "wb") as f:
                        f.write(base_image["image"])
                except:
                    pass # Skip image if extraction fails

            # --- Processing Chunks ---
            chunks = text_splitter.split_text(text)
            points = []

            if chunks:
                embeddings = model.encode(chunks, normalize_embeddings=True).tolist()

                for i, chunk in enumerate(chunks):
                    # Fixed Sparse Logic to prevent duplicate index errors
                    indices, values = get_unique_sparse_vector(chunk)

                    points.append(models.PointStruct(
                        id=generate_point_id(f"{page_num}_{i}_{chunk[:15]}"),
                        vector={
                            "default": embeddings[i],
                            "keywords": models.SparseVector(
                                indices=indices,
                                values=values
                            )
                        },
                        payload={
                            "page": page_num + 1,
                            "content": chunk,
                            "image_path": f"assets/images/{image_filename}" if image_filename else None
                        }
                    ))

            # --- Safe Upload ---
            if points:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                print(f"✅ Page {page_num+1}/{total_pages} uploaded. ({len(points)} chunks)")

        except Exception as e:
            print(f"⚠️ Error on page {page_num+1}: {str(e)}")
            continue # Keep going even if one page fails

    print("\n🎉 INGESTION COMPLETE!")

if __name__ == "__main__":
    run_ingestion()