import os
import json
import uuid
from datetime import datetime, date

_MONGO_URI = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")
db = None

if _MONGO_URI:
    try:
        from pymongo import MongoClient
        _client = MongoClient(_MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command('ping')
        db = _client.get_database("uzhavan_db")
        print("[OK] Successfully connected to MongoDB Atlas (uzhavan_db)!")
    except Exception as e:
        print(f"[WARN] MongoDB Atlas connection error (fallback to local JSON): {e}")
        db = None
else:
    print("[INFO] No MONGO_URI specified. Operating in high-speed Local JSON store mode.")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_data")
os.makedirs(DATA_DIR, exist_ok=True)

COLLECTIONS = [
    "plots",
    "crops",
    "financials",
    "livestock",
    "breeding_records",
    "milk_records",
    "market_cache",
    "settings"
]

def _json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

def _get_local_filepath(collection_name):
    return os.path.join(DATA_DIR, f"{collection_name}.json")

def _read_local_json(collection_name):
    filepath = _get_local_filepath(collection_name)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error reading local json for {collection_name}: {e}")
        return []

def _write_local_json(collection_name, items):
    filepath = _get_local_filepath(collection_name)
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False, default=_json_serial)
        os.replace(tmp_path, filepath)
    except Exception as e:
        print(f"Error writing local json for {collection_name}: {e}")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

def get_all(collection_name):
    """Retrieve all items from collection, checking MongoDB first then local JSON."""
    if db is not None:
        try:
            col = db[collection_name]
            docs = list(col.find({}))
            if docs:
                for doc in docs:
                    if "_id" in doc:
                        doc["id"] = str(doc["_id"])
                        doc.pop("_id", None)
                # Sync back to local JSON for offline caching
                _write_local_json(collection_name, docs)
                return docs
        except Exception as e:
            print(f"MongoDB get_all error for {collection_name}: {e}")

    # Fallback to local JSON
    return _read_local_json(collection_name)

def get_by_id(collection_name, item_id):
    items = get_all(collection_name)
    for item in items:
        if str(item.get("id")) == str(item_id):
            return item
    return None

def save_item(collection_name, item_data):
    """Insert or update item in MongoDB and local JSON store."""
    if not item_data.get("id"):
        item_data["id"] = str(uuid.uuid4())
    
    if "updated_at" not in item_data:
        item_data["updated_at"] = datetime.now().isoformat()
    if "created_at" not in item_data:
        item_data["created_at"] = datetime.now().isoformat()

    item_id = str(item_data["id"])

    # Update local JSON
    items = _read_local_json(collection_name)
    updated = False
    for idx, item in enumerate(items):
        if str(item.get("id")) == item_id:
            items[idx] = item_data
            updated = True
            break
    if not updated:
        items.append(item_data)
    _write_local_json(collection_name, items)

    # Sync to MongoDB Atlas
    if db is not None:
        try:
            col = db[collection_name]
            mongo_doc = dict(item_data)
            mongo_doc["_id"] = item_id
            col.replace_one({"_id": item_id}, mongo_doc, upsert=True)
        except Exception as e:
            print(f"MongoDB save_item error for {collection_name}: {e}")

    return item_data

def delete_item(collection_name, item_id):
    """Delete item from MongoDB and local JSON store."""
    item_id = str(item_id)
    items = _read_local_json(collection_name)
    items = [item for item in items if str(item.get("id")) != item_id]
    _write_local_json(collection_name, items)

    if db is not None:
        try:
            col = db[collection_name]
            col.delete_one({"_id": item_id})
        except Exception as e:
            print(f"MongoDB delete_item error for {collection_name}: {e}")
    return True

def get_settings():
    settings_list = get_all("settings")
    if settings_list:
        return settings_list[0]
    default_settings = {
        "id": "app_settings",
        "farm_name": "Uzhavan Farm (உழவன் பண்ணை)",
        "farmer_name": "Murugan K (முருகன்)",
        "district": "Thanjavur",
        "taluk": "Kumbakonam",
        "village": "Thiruvidaimarudur",
        "language": "ta",  # 'ta' or 'en'
        "currency": "INR (₹)",
        "created_at": datetime.now().isoformat()
    }
    save_item("settings", default_settings)
    return default_settings

def update_settings(data):
    current = get_settings()
    current.update(data)
    current["id"] = "app_settings"
    current["updated_at"] = datetime.now().isoformat()
    save_item("settings", current)
    return current
