from fastapi import FastAPI, HTTPException, Query
import requests
import os
import uvicorn
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="CryptoCompare API",
    description="API for retrieving cryptocurrency price data and market information from CryptoCompare",
    version="1.0.0"
)

# API Key from environment variable
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")
if not CRYPTOCOMPARE_API_KEY:
    print("⚠️ WARNING: CRYPTOCOMPARE_API_KEY is not set! API will not function correctly.")

BASE_URL = "https://min-api.cryptocompare.com/data"
HEADERS = {
    "authorization": f"Apikey {CRYPTOCOMPARE_API_KEY}"
}

@app.get("/")
def home():
    return {"message": "✅ CryptoCompare API is running!", "version": "1.0.0"}

# Helper function to send requests to CryptoCompare
async def fetch_from_cryptocompare(endpoint: str, params: Optional[Dict[str, Any]] = None):
    url = f"{BASE_URL}{endpoint}"
    
    print(f"🔍 Sending request to: {url}")
    print(f"🔍 With headers: {HEADERS}")
    print(f"🔍 With params: {params}")
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print(f"❌ Bad Request: {response.text}")
            raise HTTPException(status_code=400, detail=f"❌ Bad Request: {response.text}")
        elif response.status_code == 401:
            print(f"❌ Unauthorized: {response.text}")
            raise HTTPException(status_code=401, detail="❌ Invalid API Key")
        elif response.status_code == 429:
            print(f"❌ Too Many Requests: {response.text}")
            raise HTTPException(status_code=429, detail="❌ Rate limit exceeded. Please try again later.")
        else:
            print(f"⚠ Unexpected Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"⚠ Unexpected Error: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"❌ Connection Error: {str(e)}")

# 1️⃣ Get current price for a single symbol
@app.get("/price")
async def get_price(
    fsym: str = Query(..., description="From Symbol (e.g., BTC)"),
    tsyms: str = Query(..., description="To Symbol(s), comma separated (e.g., USD,EUR)"),
    e: Optional[str] = Query(None, description="Exchange (e.g., Coinbase)")
):
    """
    Get the current price of a cryptocurrency in multiple currencies
    """
    params = {
        "fsym": fsym.upper(),
        "tsyms": tsyms.upper()
    }
    
    if e:
        params["e"] = e
    
    return await fetch_from_cryptocompare("/price", params)

# 2️⃣ Get historical daily data
@app.get("/histoday")
async def get_histoday(
    fsym: str = Query(..., description="From Symbol (e.g., BTC)"),
    tsym: str = Query(..., description="To Symbol (e.g., USD)"),
    limit: Optional[int] = Query(30, description="Number of data points (max 2000)"),
    aggregate: Optional[int] = Query(1, description="Aggregation level"),
    e: Optional[str] = Query(None, description="Exchange")
):
    """
    Get historical daily OHLCV data
    """
    params = {
        "fsym": fsym.upper(),
        "tsym": tsym.upper(),
        "limit": min(limit, 2000),
        "aggregate": aggregate
    }
    
    if e:
        params["e"] = e
    
    return await fetch_from_cryptocompare("/v2/histoday", params)

# 3️⃣ Get historical hourly data
@app.get("/histohour")
async def get_histohour(
    fsym: str = Query(..., description="From Symbol (e.g., BTC)"),
    tsym: str = Query(..., description="To Symbol (e.g., USD)"),
    limit: Optional[int] = Query(24, description="Number of data points (max 2000)"),
    aggregate: Optional[int] = Query(1, description="Aggregation level"),
    e: Optional[str] = Query(None, description="Exchange")
):
    """
    Get historical hourly OHLCV data
    """
    params = {
        "fsym": fsym.upper(),
        "tsym": tsym.upper(),
        "limit": min(limit, 2000),
        "aggregate": aggregate
    }
    
    if e:
        params["e"] = e
    
    return await fetch_from_cryptocompare("/v2/histohour", params)

# 4️⃣ Get top pairs for a coin
@app.get("/top-pairs")
async def get_top_pairs(
    fsym: str = Query(..., description="From Symbol (e.g., BTC)"),
    limit: Optional[int] = Query(10, description="Number of pairs to return (max 100)")
):
    """
    Get top trading pairs for a cryptocurrency
    """
    params = {
        "fsym": fsym.upper(),
        "limit": min(limit, 100)
    }
    
    return await fetch_from_cryptocompare("/top/pairs", params)

# 5️⃣ Get latest news with improved response handling
@app.get("/news")
async def get_news(
    categories: Optional[str] = Query(None, description="Categories (e.g., BTC,Regulation)"),
    limit: Optional[int] = Query(5, description="Number of news items (max 20)"),
    lang: Optional[str] = Query("EN", description="Language (e.g., EN,PT,ES)")
):
    """
    Get latest cryptocurrency news with simplified response format
    """
    params = {
        "limit": min(limit, 20),  # Reduce default and max limit
        "lang": lang.upper()
    }
    
    if categories:
        params["categories"] = categories
    
    full_response = await fetch_from_cryptocompare("/v2/news/", params)
    
    # Extract only the essential information to reduce response size
    simplified_news = []
    
    if "Data" in full_response and isinstance(full_response["Data"], list):
        for item in full_response["Data"][:limit]:
            simplified_news.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "url": item.get("url"),
                "source": item.get("source"),
                "published_on": item.get("published_on"),
                "categories": item.get("categories", "").split("|"),
                "tags": item.get("tags", "").split("|") if item.get("tags") else []
            })
    
    return {
        "status": "success",
        "count": len(simplified_news),
        "news": simplified_news
    }    
    
# 6️⃣ Get multiple symbols price
@app.get("/pricemulti")
async def get_pricemulti(
    fsyms: str = Query(..., description="From Symbols, comma separated (e.g., BTC,ETH)"),
    tsyms: str = Query(..., description="To Symbols, comma separated (e.g., USD,EUR)"),
    e: Optional[str] = Query(None, description="Exchange")
):
    """
    Get prices for multiple cryptocurrencies in multiple currencies
    """
    params = {
        "fsyms": fsyms.upper(),
        "tsyms": tsyms.upper()
    }
    
    if e:
        params["e"] = e
    
    return await fetch_from_cryptocompare("/pricemulti", params)

# 7️⃣ Test the API key
@app.get("/test-api-key")
async def test_api_key():
    """
    Test the CryptoCompare API key
    """
    try:
        # Use a simple price request to test the API key
        result = await fetch_from_cryptocompare("/price", {"fsym": "BTC", "tsyms": "USD"})
        return {
            "status": "success", 
            "message": "✅ API key is valid and connection to CryptoCompare is established",
            "price": result
        }
    except Exception as e:
        return {"status": "error", "message": f"❌ Connection Error: {str(e)}"}

# Run the server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8085))  # Using port 8085 to avoid conflicts with other APIs
    print(f"🚀 Starting CryptoCompare API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
