import json
import os
import time
from decimal import Decimal

CACHE_FILE = "sorted_coins.json"
CACHE_EXPIRATION = 6 * 3600  # 6 hours in seconds

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float before saving
        return super().default(obj)

def load_cached_sorted_symbols():
    """Load sorted symbols from cache if valid."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                if time.time() - data["timestamp"] < CACHE_EXPIRATION:
                    return data["sorted_coins"]  # ✅ Use cached data if valid
        except Exception as e:
            print(f"⚠️ Error reading cache: {e}, recalculating...")
    return None  # If cache is invalid, return None

def save_sorted_symbols(sorted_coins):
    """Save sorted symbols to cache, ensuring all values are JSON serializable."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"timestamp": time.time(), "sorted_coins": sorted_coins}, f, cls=DecimalEncoder)
    except Exception as e:
        print(f"⚠️ Error saving cache: {e}")