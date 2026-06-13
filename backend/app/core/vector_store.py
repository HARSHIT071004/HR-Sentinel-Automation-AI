import os
import json
import copy
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
        self._vectors = []  # keep original vectors for rebuild
        self._load()

    def _load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.metadata = data
                self._vectors = []
            elif isinstance(data, dict):
                self.metadata = data.get("metadata", [])
                self._vectors = data.get("vectors", [])
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
            self._vectors = []

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        data = {"metadata": self.metadata, "vectors": self._vectors}
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, cls=_NumpyEncoder)

    def add(self, embeddings: list[list[float]], metadatas: list[dict], texts: list[str]):
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        for i, (meta, text) in enumerate(zip(metadatas, texts)):
            meta["text"] = text
            self.metadata.append(meta)
            self._vectors.append(embeddings[i])
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
                meta = copy.deepcopy(self.metadata[idx])
                meta["score"] = float(dist)
                results.append(meta)
        return results

    def delete_by_filter(self, key: str, value: str) -> int:
        """Delete all entries where metadata[key] == value. Returns count removed."""
        before = len(self.metadata)
        keep_indices = [i for i, m in enumerate(self.metadata) if m.get(key) != value]
        if len(keep_indices) == before:
            return 0
        self.metadata = [self.metadata[i] for i in keep_indices]
        self._vectors = [self._vectors[i] for i in keep_indices]
        self.index = faiss.IndexFlatIP(self.dimension)
        if self._vectors:
            vectors = np.array(self._vectors, dtype=np.float32)
            faiss.normalize_L2(vectors)
            self.index.add(vectors)
        self._save()
        return before - len(self.metadata)

    def count(self) -> int:
        return self.index.ntotal


class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32):
            return float(obj)
        return super().default(obj)


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

    def delete_documents(self, collection: str, key: str, value: str) -> int:
        store = self.get_store(collection)
        return store.delete_by_filter(key, value)

    def list_collections(self) -> list[str]:
        return [f.replace(".index", "") for f in os.listdir(FAISS_DIR) if f.endswith(".index")]


vector_store = VectorStoreManager()
