from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile
from starlette.middleware.cors import CORSMiddleware

from routes import accounts_router, fe_router, orders_router, profiles_router, shopping_carts_router
from routes.movies import router as movies_router
from routes.payments import router as payments_router

app = FastAPI(
    title="Online Cinema API",
    description="Description of project",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router,
    prefix=f"{api_version_prefix}/accounts",
    tags=["Accounts"],
)
app.include_router(fe_router, prefix="/fe")
app.include_router(
    shopping_carts_router,
    prefix=f"{api_version_prefix}/shopping-carts",
    tags=["Shopping carts"],
)
app.include_router(
    movies_router,
    prefix=f"{api_version_prefix}/movies",
    tags=["Movies"],
)
app.include_router(
    profiles_router,
    prefix=f"{api_version_prefix}/profiles",
    tags=["Profiles"],
)
app.include_router(
    orders_router,
    prefix=f"{api_version_prefix}/orders",
    tags=["Orders"],
)
app.include_router(
    payments_router,
    prefix=f"{api_version_prefix}/payments",
    tags=["Payments"],
)
