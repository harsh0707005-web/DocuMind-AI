"""MongoDB database connection and helpers with local JSON fallback."""

import os
import json
import uuid
import certifi
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client: AsyncIOMotorClient = None
db = None
_use_local = False

# Local JSON fallback path
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), "local_db.json")


class LocalDB:
    """Simple JSON-file-based DB fallback when MongoDB is unavailable."""

    def __init__(self, path):
        self.path = path
        self.data = {"documents": [], "conversations": [], "messages": []}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def insert_one(self, collection: str, doc: dict) -> str:
        doc_id = str(uuid.uuid4())
        doc["_id"] = doc_id
        self.data.setdefault(collection, []).append(doc)
        self._save()
        return doc_id

    def find(self, collection: str, query: dict = None, sort_key: str = None, sort_dir: int = -1, limit: int = None):
        items = self.data.get(collection, [])
        if query:
            items = [i for i in items if all(i.get(k) == v for k, v in query.items())]
        if sort_key:
            items = sorted(items, key=lambda x: x.get(sort_key, ""), reverse=(sort_dir == -1))
        if limit:
            items = items[:limit]
        return items

    def find_one(self, collection: str, doc_id: str):
        for item in self.data.get(collection, []):
            if item.get("_id") == doc_id:
                return item
        return None

    def update_one(self, collection: str, doc_id: str, update: dict):
        for item in self.data.get(collection, []):
            if item.get("_id") == doc_id:
                if "$set" in update:
                    item.update(update["$set"])
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        item[k] = item.get(k, 0) + v
                self._save()
                return True
        return False

    def delete_one(self, collection: str, doc_id: str) -> bool:
        items = self.data.get(collection, [])
        for i, item in enumerate(items):
            if item.get("_id") == doc_id:
                items.pop(i)
                self._save()
                return True
        return False

    def delete_many(self, collection: str, query: dict = None):
        if query is None:
            self.data[collection] = []
        else:
            self.data[collection] = [
                i for i in self.data.get(collection, [])
                if not all(i.get(k) == v for k, v in query.items())
            ]
        self._save()


local_db = LocalDB(LOCAL_DB_PATH)


async def connect_db():
    """Connect to MongoDB, fall back to local JSON DB on failure."""
    global client, db, _use_local
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        db = client[settings.DATABASE_NAME]
        # Test connection
        await db.command("ping")
        print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
        _use_local = False
    except Exception as e:
        print(f"⚠️  MongoDB unavailable: {e}")
        print("📂 Using local JSON database as fallback")
        _use_local = True


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


def get_db():
    """Get database instance."""
    return db


def is_local():
    """Check if using local fallback."""
    return _use_local


def get_local_db() -> LocalDB:
    """Get local DB instance."""
    return local_db
