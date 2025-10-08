# main.py

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, admin, portfolios
from core.config import FRONTEND_URL

app = FastAPI(
    title="Portfolio Backend",
    version="1.0.0",
    description="FastAPI backend for portfolio management with user authentication.",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_tags=[
        {"name": "Auth", "description": "Kayıt, giriş, doğrulama işlemleri"},
        {"name": "Admin", "description": "Yönetici işlemleri"},
        {"name": "Users", "description": "Kullanıcı profili yönetimi"},
        {"name": "Portfolios", "description": "Portfolyo CRUD işlemleri"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(portfolios.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )