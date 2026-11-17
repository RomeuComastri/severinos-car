from fastapi import Depends, FastAPI

from app.core.config import get_settings
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.router import router as auth_router
from app.modules.health.router import router as health_router
from app.modules.veiculos.router import router as veiculos_router

# from app.modules.compradores.router import router as compradores_router
# from app.modules.vendas.router import router as vendas_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API de controle para lojas de carros.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(veiculos_router, dependencies=[Depends(get_current_user)])
# app.include_router(compradores_router, dependencies=[Depends(get_current_user)])
# app.include_router(vendas_router, dependencies=[Depends(get_current_user)])


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs"}
