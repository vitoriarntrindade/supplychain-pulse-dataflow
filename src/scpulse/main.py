from fastapi import FastAPI
from scpulse.api.routes import health

app = FastAPI(
    title="SupplyChain Pulse",
    description="API de monitoramento logístico em tempo real",
    version="0.1.0",
)

# Registro das rotas
app.include_router(health.router, prefix="/api")
