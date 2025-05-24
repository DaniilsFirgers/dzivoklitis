from fastapi import FastAPI
from backend.api.routes.filters import router as filter_router
from backend.api.routes.favourites import router as favourite_router

app = FastAPI(title="Dzivoklitis API", version="0.1.0")

app.include_router(filter_router, prefix="/filters", tags=["Filters"])
app.include_router(favourite_router, prefix="/favourites", tags=["Favourites"])
