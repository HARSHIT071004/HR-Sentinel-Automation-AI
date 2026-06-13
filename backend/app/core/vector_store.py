import os
import json
import numpy as np
import faiss
import logging

logger = logging.getLogger(__name__)

FAISS_DIR = "./faiss_data"
os.makedirs(FAISS_DIR, exist_ok=True)


class FAISSVectorStore:
    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self.index_path = os.path.join(FAISS_DIR, f"{collection_name}.index")
        self.meta_path = os.path.join(FAISS_DIR, f"{collection_name}_meta.json")
        self.dimension = 1536  # OpenAI text-embedding-3-small
        self.index = None
        self.metadata = []
        self._load()

    def _load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)

    def add(self, embeddings: list[list[float]], metadatas: list[dict], texts: list[str]):
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        for i, (meta, text) in enumerate(zip(metadatas, texts)):
            meta["text"] = text
            self.metadata.append(meta)
        self._save()

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        distances, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                meta = self.metadata[idx].copy()
                meta["score"] = float(dist)
                results.append(meta)
        return results

    def count(self) -> int:
        return self.index.ntotal


class VectorStoreManager:
    def __init__(self):
        self.stores = {}

    def get_store(self, name: str = "default") -> FAISSVectorStore:
        if name not in self.stores:
            self.stores[name] = FAISSVectorStore(name)
        return self.stores[name]

    def add_documents(self, collection: str, texts: list[str], metadatas: list[dict], embeddings: list[list[float]]):
        store = self.get_store(collection)
        store.add(embeddings, metadatas, texts)

    def search(self, collection: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        store = self.get_store(collection)
        return store.search(query_embedding, top_k)

    def list_collections(self) -> list[str]:
        return [f.replace(".index", "") for f in os.listdir(FAISS_DIR) if f.endswith(".index")]


vector_store = VectorStoreManager()
