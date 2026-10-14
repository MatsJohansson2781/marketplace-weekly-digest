from typing import Literal

from typing import Annotated

from pydantic import BaseModel, Field


EmailAddress = Annotated[str, Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class SellerAsset(BaseModel):
    seller_name: str
    title: str
    storefront_url: str
    status: Literal["published", "draft"]


class BuyerUpdate(BaseModel):
    buyer_email: EmailAddress
    topic: str
    detail: str


class OrderHandoff(BaseModel):
    order_number: str
    buyer_email: EmailAddress
    seller_name: str
    next_step: str
    ready: bool


class DigestRequest(BaseModel):
    audience_email: EmailAddress
    week_label: str
    seller_assets: list[SellerAsset] = Field(default_factory=list)
    buyer_updates: list[BuyerUpdate] = Field(default_factory=list)
    order_handoffs: list[OrderHandoff] = Field(default_factory=list)


class DigestResult(BaseModel):
    recipient: EmailAddress
    subject: str
    lines: list[str]


class ScheduleRequest(BaseModel):
    task_url: str
    cron_expr: str = "0 9 * * 1"


class ScheduleResult(BaseModel):
    job_id: str
