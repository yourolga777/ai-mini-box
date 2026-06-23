from fastapi import APIRouter

from ai_mini_box_web.services.help_manager import get_all

router = APIRouter()


@router.get("/api/help")
def list_help():
    return get_all()
