from fastapi import FastAPI

from app.api.assets import router as assets_router
from app.database import init_db

app = FastAPI(title="Asset Tool API")

init_db()

app.include_router(assets_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
