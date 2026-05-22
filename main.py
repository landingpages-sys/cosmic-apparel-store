from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
import os

from routes import printify_routes, newsletter_routes, meta_ads_routes, orders_routes

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shopify POD Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(printify_routes.router, prefix="/api/printify")
app.include_router(newsletter_routes.router, prefix="/api/newsletter")
app.include_router(meta_ads_routes.router, prefix="/api/meta-ads")
app.include_router(orders_routes.router, prefix="/api/orders")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("POD Backend started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
