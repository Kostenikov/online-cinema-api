from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import get_settings

router = APIRouter()

settings = get_settings()
templates = Jinja2Templates(directory=Path(__file__).parent.parent.joinpath("templates"))


@router.get(
    "/activate_page/",
    name="activate_page",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def activation_page(
    token: str,
    request: Request,
):
    activation_url = request.url_for("activate_account")
    return templates.TemplateResponse(
        "activation_fe_page.html",
        {"request": request, "activation_url": activation_url, "token": token},
    )
