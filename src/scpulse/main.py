from fastapi import FastAPI
from src.scpulse.api.routes import orders, inventory, suppliers

app = FastAPI(title="SupplyChain Pulse API")

app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
