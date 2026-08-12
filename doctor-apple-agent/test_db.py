from app.config import settings
from app.database import MongoStore

print("Database:", settings.mongodb_database)
print("Offline mode:", settings.offline_mode)

store = MongoStore()

try:
    store.client.admin.command("ping")
    print("MongoDB CONNECTED!")
except Exception as e:
    print("MongoDB FAILED:")
    print(repr(e))