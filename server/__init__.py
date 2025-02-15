import threading
import time

CACHE_UPDATE_INTERVAL = 300  # Every 5 minutes (adjust as needed)

def update_sorted_symbols(client):
    """Background thread to continuously update sorted symbols."""
    from bot.coins import get_sorted_symbols
    while True:
        try:
            get_sorted_symbols(client)  # Updates the cache
            print("✅ Cached sorted symbols updated!")
        except Exception as e:
            print(f"⚠️ Error updating sorted symbols: {e}")
        
        time.sleep(CACHE_UPDATE_INTERVAL)  # Wait before updating again

# ✅ Start background thread when bot runs
def start_background_cache_update(client):
    print("🔄 Starting background cache update thread...")
    cache_thread = threading.Thread(target=update_sorted_symbols, args=(client,), daemon=True)
    cache_thread.start()
