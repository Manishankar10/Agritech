import os
import json
import uuid
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

_MONGO_URI = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")
db = None

if _MONGO_URI:
    try:
        from pymongo import MongoClient
        _client = MongoClient(_MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command('ping')
        custom_db = os.environ.get("MONGO_DB_NAME")
        if custom_db:
            db = _client.get_database(custom_db.strip())
        else:
            try:
                def_db = _client.get_default_database()
                if def_db is not None and def_db.name not in ("admin", "local", "config", "test", "capital_desk"):
                    db = def_db
                else:
                    db = _client.get_database("uzhavan_db")
            except Exception:
                db = _client.get_database("uzhavan_db")
        print(f"[OK] Successfully connected to MongoDB Atlas database: '{db.name}'!")
    except Exception as e:
        print(f"[WARN] MongoDB Atlas connection error (fallback to local JSON): {e}")
        db = None
else:
    print("[INFO] No MONGO_URI specified. Operating in high-speed Local JSON store mode.")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_data")
os.makedirs(DATA_DIR, exist_ok=True)

COLLECTIONS = [
    "users",
    "plots",
    "crops",
    "financials",
    "livestock",
    "breeding_records",
    "milk_records",
    "market_cache"
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
                _write_local_json(collection_name, docs)
                return docs
            else:
                # If collection is empty in MongoDB, seed from local JSON if available
                local_docs = _read_local_json(collection_name)
                if local_docs:
                    for d in local_docs:
                        m_doc = dict(d)
                        m_id = str(d.get("id") or uuid.uuid4())
                        m_doc["_id"] = m_id
                        col.replace_one({"_id": m_id}, m_doc, upsert=True)
                    return local_docs
                return []
        except Exception as e:
            print(f"MongoDB get_all error for {collection_name}: {e}")

    return _read_local_json(collection_name)

def get_by_id(collection_name, item_id):
    if not item_id:
        return None
    item_id = str(item_id)
    if db is not None:
        try:
            col = db[collection_name]
            doc = col.find_one({"$or": [{"_id": item_id}, {"id": item_id}]})
            if doc:
                if "_id" in doc:
                    doc["id"] = str(doc["_id"])
                    doc.pop("_id", None)
                return doc
        except Exception as e:
            print(f"MongoDB get_by_id error for {collection_name}: {e}")

    items = get_all(collection_name)
    for item in items:
        if str(item.get("id")) == item_id:
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

    if db is not None:
        try:
            col = db[collection_name]
            mongo_doc = dict(item_data)
            mongo_doc["_id"] = item_id
            col.replace_one({"_id": item_id}, mongo_doc, upsert=True)
        except Exception as e:
            print(f"MongoDB save_item error for {collection_name}: {e}")

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

    return item_data

def delete_item(collection_name, item_id):
    """Delete item from MongoDB and local JSON store."""
    item_id = str(item_id)
    if db is not None:
        try:
            col = db[collection_name]
            col.delete_one({"$or": [{"_id": item_id}, {"id": item_id}]})
        except Exception as e:
            print(f"MongoDB delete_item error for {collection_name}: {e}")

    items = _read_local_json(collection_name)
    items = [item for item in items if str(item.get("id")) != item_id]
    _write_local_json(collection_name, items)
    return True

# ========================================================
# USER AUTHENTICATION & LOCATION PREFERENCE STORE
# ========================================================

def get_user_by_username(username):
    if not username:
        return None
    uname = username.strip().lower()

    if db is not None:
        try:
            col = db["users"]
            doc = col.find_one({"$or": [{"username": uname}, {"id": uname}, {"_id": uname}]})
            if doc:
                if "_id" in doc:
                    doc["id"] = str(doc["_id"])
                    doc.pop("_id", None)
                return doc
            if col.count_documents({}) == 0:
                get_all("users")
                doc = col.find_one({"$or": [{"username": uname}, {"id": uname}, {"_id": uname}]})
                if doc:
                    if "_id" in doc:
                        doc["id"] = str(doc["_id"])
                        doc.pop("_id", None)
                    return doc
        except Exception as e:
            print(f"MongoDB get_user_by_username error: {e}")

    users = get_all("users")
    for u in users:
        if u.get("username", "").lower() == uname or str(u.get("id", "")).lower() == uname:
            return u
    return None

def create_user(username, password, farmer_name, farm_name, district, taluk="", village="", language="en"):
    uname = username.strip().lower()
    if get_user_by_username(uname):
        return None, "Username already exists. Please choose another or login."

    user_doc = {
        "id": uname,
        "username": uname,
        "password_hash": generate_password_hash(password),
        "farmer_name": farmer_name.strip() or uname.capitalize(),
        "farm_name": farm_name.strip() or f"{farmer_name}'s Farm",
        "district": district.strip() or "Thanjavur",
        "taluk": taluk.strip(),
        "village": village.strip(),
        "language": language or "en",
        "created_at": datetime.now().isoformat()
    }
    save_item("users", user_doc)
    return user_doc, None

def authenticate_user(username, password):
    user = get_user_by_username(username)
    if not user:
        return None
    if check_password_hash(user.get("password_hash", ""), password):
        return user
    return None

def update_user_profile(username, update_data):
    user = get_user_by_username(username)
    if not user:
        return None
    
    update_data.pop("username", None)
    update_data.pop("id", None)
    
    if "password" in update_data and update_data["password"]:
        user["password_hash"] = generate_password_hash(update_data["password"])
        update_data.pop("password", None)

    user.update(update_data)
    user["updated_at"] = datetime.now().isoformat()
    save_item("users", user)
    return user

# ========================================================
# USER-SCOPED ENTITY HELPERS (DATA ISOLATED BY LOGIN)
# ========================================================

def get_user_items(collection_name, username):
    """Retrieves all items belonging specifically to the logged-in user."""
    if not username:
        return get_all(collection_name)
    uname = username.strip().lower()

    if db is not None:
        try:
            col = db[collection_name]
            if uname == "farmer":
                query = {"$or": [{"user_id": uname}, {"user_id": "farmer"}, {"user_id": {"$exists": False}}]}
            else:
                query = {"user_id": uname}
            docs = list(col.find(query))
            if docs:
                for doc in docs:
                    if "_id" in doc:
                        doc["id"] = str(doc["_id"])
                        doc.pop("_id", None)
                return docs
            # If collection is completely empty in MongoDB, trigger seed check
            if col.count_documents({}) == 0:
                get_all(collection_name)
                docs = list(col.find(query))
                for doc in docs:
                    if "_id" in doc:
                        doc["id"] = str(doc["_id"])
                        doc.pop("_id", None)
                return docs
            return []
        except Exception as e:
            print(f"MongoDB get_user_items error for {collection_name}: {e}")

    all_items = get_all(collection_name)
    return [i for i in all_items if i.get("user_id", "farmer").lower() == uname]

def save_user_item(collection_name, item_data, username):
    if username:
        item_data["user_id"] = username.strip().lower()
    return save_item(collection_name, item_data)

def delete_user_item(collection_name, item_id, username):
    item = get_by_id(collection_name, item_id)
    if not item:
        return False
    if username and item.get("user_id", "farmer").lower() != username.strip().lower():
        return False # Permission denied
    return delete_item(collection_name, item_id)
