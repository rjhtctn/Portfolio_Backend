import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, admin, portfolios

app = FastAPI(
    title="Portfolio Backend",
    version="1.0.0",
    description="FastAPI backend for portfolio management with user authentication.",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_tags=[
        {"name": "Auth", "description": "Kayıt, giriş, doğrulama işlemleri"},
        {"name": "Users", "description": "Kullanıcı profili yönetimi"},
        {"name": "Portfolios", "description": "Portfolyo CRUD işlemleri"},
    ]
)

app.openapi_schema = None

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(portfolios.router)