from fastapi import FastAPI

from routes import accounts_router, fe_router
from routes.movies import router as movies_router

app = FastAPI(
    title="Online Cinema API",
    description="Description of project",
)

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router,
    prefix=f"{api_version_prefix}/accounts",
    tags=["Accounts"],
)
app.include_router(fe_router, prefix="/fe")

app.include_router(
    movies_router,
    prefix=f"{api_version_prefix}/movies",
    tags=["Movies"],
)
