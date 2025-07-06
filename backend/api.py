from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from typing import Dict, Any, List
import asyncio
import threading
from main import find_stocks_in_x_strategies

app = FastAPI()



# Cache for storing results
cache = {
    "data": {},
    "last_updated": None,
    "is_loading": False
}

def background_fetch():
    """Fetch data in background for common strategy counts"""
    global cache
    if cache["is_loading"]:
        return
    
    cache["is_loading"] = True
    print("🔄 Starting background data fetch...")
    
    try:
        # Pre-fetch common strategy counts
        for min_strat in [2, 3, 4]:
            print(f"📊 Fetching stocks for {min_strat}+ strategies...")
            result = find_stocks_in_x_strategies(min_strat)
            if not result.empty:
                cache["data"][min_strat] = result.to_dict('records')
                print(f"✅ Cached {len(cache['data'][min_strat])} stocks for {min_strat}+ strategies")
        
        cache["last_updated"] = pd.Timestamp.now()
        print("🎉 Background fetch completed!")
        
    except Exception as e:
        print(f"❌ Background fetch error: {e}")
    finally:
        cache["is_loading"] = False

async def periodic_cache_refresh():
    """Periodically refresh cache every 3 hours"""
    while True:
        try:
            # Wait 3 hours (10800 seconds)
            await asyncio.sleep(10800)
            
            print("⏰ 3-hour cache refresh triggered...")
            
            # Run the background fetch in a thread to avoid blocking
            def refresh_cache():
                background_fetch()
            
            thread = threading.Thread(target=refresh_cache, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"❌ Periodic cache refresh error: {e}")
            # Continue the loop even if there's an error
            await asyncio.sleep(60)  # Wait 1 minute before retrying

# Start background fetch on startup
@app.on_event("startup")
async def startup_event():
    # Run initial background fetch in a separate thread
    thread = threading.Thread(target=background_fetch, daemon=True)
    thread.start()
    
    # Start periodic cache refresh task
    asyncio.create_task(periodic_cache_refresh())
    print("🕐 Started periodic cache refresh (every 3 hours)")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    min_strategies: int

@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "API is running"}

@app.get("/status")
def get_status() -> Dict[str, Any]:
    """Check loading status and cache info"""
    return {
        "is_loading": cache["is_loading"],
        "cached_strategies": list(cache["data"].keys()),
        "last_updated": cache["last_updated"].isoformat() if cache["last_updated"] else None,
        "cache_size": len(cache["data"])
    }

@app.post("/refresh-cache")
def refresh_cache_endpoint() -> Dict[str, Any]:
    """Manually trigger cache refresh"""
    if cache["is_loading"]:
        return {
            "success": False,
            "message": "Cache refresh already in progress"
        }
    
    # Start refresh in background thread
    thread = threading.Thread(target=background_fetch, daemon=True)
    thread.start()
    
    return {
        "success": True,
        "message": "Cache refresh triggered successfully"
    }

@app.post("/search")
def search_stocks(request: SearchRequest) -> Dict[str, Any]:
    try:
        if request.min_strategies < 2:
            return {
                "success": False,
                "message": "Minimum strategies must be at least 2",
                "data": [],
                "total": 0
            }
        
        # Check if we have cached data
        if request.min_strategies in cache["data"]:
            data = cache["data"][request.min_strategies]
            return {
                "success": True,
                "message": f"Found {len(data)} stocks in {request.min_strategies}+ strategies (cached)",
                "data": data,
                "total": len(data),
                "from_cache": True
            }
        
        # If not cached, fetch fresh data
        print(f"🔍 Fetching fresh data for {request.min_strategies}+ strategies...")
        result = find_stocks_in_x_strategies(request.min_strategies)
        
        if result.empty:
            return {
                "success": False,
                "message": f"No stocks found in {request.min_strategies}+ strategies",
                "data": [],
                "total": 0,
                "from_cache": False
            }
        
        # Convert DataFrame to list of dictionaries
        data: List[Dict[str, Any]] = result.to_dict('records')
        
        # Clean up any problematic values
        for record in data:
            for key, value in record.items():
                if isinstance(value, float):
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        record[key] = None
        
        # Cache the result
        cache["data"][request.min_strategies] = data
        
        return {
            "success": True,
            "message": f"Found {len(data)} stocks in {request.min_strategies}+ strategies",
            "data": data,
            "total": len(data),
            "from_cache": False
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": [],
            "total": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
