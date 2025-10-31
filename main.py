from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import init_db
from endpoints.get_endpoints import get_router
from endpoints.delete_endpoints import delete_router
from endpoints.post_endpoints import post_router
from endpoints.patch_endpoints import patch_router

app = FastAPI()

#for debugging
origins = [
    "http://192.168.0.74:5173",
    "http://localhost:5173" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],       
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app.include_router(get_router)
app.include_router(delete_router)
app.include_router(post_router)
app.include_router(patch_router)