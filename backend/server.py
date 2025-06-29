from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import random
import string
import validators


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class UrlCreate(BaseModel):
    original_url: str

class UrlResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_url: str
    short_code: str
    short_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    click_count: int = 0

class ClickRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    short_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


def generate_short_code(length=6):
    """Generate a random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


async def get_unique_short_code():
    """Generate a unique short code that doesn't exist in database"""
    while True:
        code = generate_short_code()
        existing = await db.urls.find_one({"short_code": code})
        if not existing:
            return code


@api_router.post("/shorten", response_model=UrlResponse)
async def create_short_url(url_data: UrlCreate):
    # Validate URL
    original_url = url_data.original_url.strip()
    
    # Add http:// if no protocol is specified
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'https://' + original_url
    
    if not validators.url(original_url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    # Generate unique short code
    short_code = await get_unique_short_code()
    
    # Create URL object
    url_obj = UrlResponse(
        original_url=original_url,
        short_code=short_code,
        short_url=f"domain.com/{short_code}"  # This will be dynamic in production
    )
    
    # Save to database
    await db.urls.insert_one(url_obj.dict())
    
    return url_obj


@api_router.get("/urls", response_model=List[UrlResponse])
async def get_all_urls():
    """Get all shortened URLs - for testing purposes"""
    urls = await db.urls.find().to_list(1000)
    return [UrlResponse(**url) for url in urls]


# Redirect endpoint (not under /api prefix)
@app.get("/{short_code}")
async def redirect_url(short_code: str):
    # Find URL by short code
    url_record = await db.urls.find_one({"short_code": short_code})
    
    if not url_record:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    # Update click count
    await db.urls.update_one(
        {"short_code": short_code},
        {"$inc": {"click_count": 1}}
    )
    
    # Record click for analytics
    click_record = ClickRecord(
        short_code=short_code,
        # user_agent and ip_address can be added later for analytics
    )
    await db.clicks.insert_one(click_record.dict())
    
    # Redirect to original URL
    return RedirectResponse(url=url_record["original_url"], status_code=302)


@api_router.get("/stats/{short_code}")
async def get_url_stats(short_code: str):
    """Get statistics for a short URL"""
    url_record = await db.urls.find_one({"short_code": short_code})
    
    if not url_record:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    # Get click records
    clicks = await db.clicks.find({"short_code": short_code}).to_list(1000)
    
    # Group clicks by date
    daily_clicks = {}
    for click in clicks:
        date_str = click["timestamp"].strftime("%Y-%m-%d")
        daily_clicks[date_str] = daily_clicks.get(date_str, 0) + 1
    
    return {
        "short_code": short_code,
        "original_url": url_record["original_url"],
        "total_clicks": len(clicks),
        "daily_clicks": daily_clicks,
        "created_at": url_record["created_at"]
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()