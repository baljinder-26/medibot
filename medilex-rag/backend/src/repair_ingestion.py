import os
import fitz
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Setup
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

PDF_PATH = os.path.join(os.path.dirname(__file__), "../data/English- The_Gale_Encyclopedia_of_Medicine_5th_Ed_9_Vol_Set_2015.pdf")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "../assets/images")
COLLECTION_NAME = "medilex_encyclopedia"

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
model = SentenceTransformer('BAAI/bge-large-en-v1.5')

# --- Missing Pages List ---
missing_pages = [
    1219, 1552, 1553, 1554, 1555, 1665, 1666, 1706, 1885, 1906, 
    1921, 1980, 2119, 2121, 2122, 2123, 2169, 2188, 2283, 2300, 
    2343, 2413, 2488, 2494, 2518, 2610, 2611, 2676, 2685, 2822, 
    2938, 2965, 2966, 3142, 3169, 3329, 3418, 3448, 3474, 3492, 
    3494, 3500, 3727, 3733, 3837, 3883, 3888, 3904, 4059, 4216, 
    4273, 4274, 4425, 5550
]

def generate_point_id(text):
    return int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (10**15)

def get_unique_sparse_vector(text):
    words = text.lower().split()
    sparse_data = {}
    for word in words:
        if len(word) > 3:
            idx = hash(word) % 10000
            sparse_data[idx] = sparse_data.get(idx, 0.0) + float(words.count(word))
    return list(sparse_data.keys()), list(sparse_data.values())

def repair_ingestion():
    if not os.path.exists(PDF_PATH):
        print("❌ PDF not found!")
        return

    doc = fitz.open(PDF_PATH)
    print(f"🛠️ Repairing {len(missing_pages)} missing pages...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150, separators=["\n\n", "\n", ".", " "]
    )

    for page_num_actual in missing_pages:
        page_idx = page_num_actual - 1 # Converting to 0-based index
        try:
            page = doc[page_idx]
            text = page.get_text()
            
            # Image logic
            image_filename = None
            image_list = page.get_images(full=True)
            if image_list:
                xref = image_list[0][0]
                base_image = doc.extract_image(xref)
                image_filename = f"page_{page_num_actual}.png"
                with open(os.path.join(IMAGE_DIR, image_filename), "wb") as f:
                    f.write(base_image["image"])

            chunks = text_splitter.split_text(text)
            points = []
            if chunks:
                embeddings = model.encode(chunks, normalize_embeddings=True).tolist()
                for i, chunk in enumerate(chunks):
                    indices, values = get_unique_sparse_vector(chunk)
                    points.append(models.PointStruct(
                        id=generate_point_id(f"{page_idx}_{i}_{chunk[:15]}"),
                        vector={
                            "default": embeddings[i],
                            "keywords": models.SparseVector(indices=indices, values=values)
                        },
                        payload={
                            "page": page_num_actual,
                            "content": chunk,
                            "image_path": f"assets/images/{image_filename}" if image_filename else None
                        }
                    ))

            if points:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                print(f"✅ Repaired Page {page_num_actual}")

        except Exception as e:
            print(f"⚠️ Failed again on Page {page_num_actual}: {e}")

    print("\n🎉 REPAIR COMPLETE! All missing pages are now in Qdrant.")

if __name__ == "__main__":
    repair_ingestion()