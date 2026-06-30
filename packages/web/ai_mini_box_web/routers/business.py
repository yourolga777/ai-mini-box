from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_mini_box.core.models import BusinessConfig
from ai_mini_box.infrastructure.business_config import load_business_config, save_business_config

router = APIRouter()


@router.get("/config")
def get_business_config() -> BusinessConfig:
    return load_business_config()


class BusinessConfigUpdate(BaseModel):
    company_name: str | None = None
    work_hours: str | None = None
    delivery_info: str | None = None
    return_policy: str | None = None
    payment_methods: str | None = None
    contacts: str | None = None
    faq: list[dict] | None = None


@router.put("/config")
def update_business_config(body: BusinessConfigUpdate) -> BusinessConfig:
    cfg = load_business_config()
    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(cfg, key, value)
    save_business_config(cfg)
    return load_business_config()
