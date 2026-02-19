import uuid

from pydantic import BaseModel, Field


class PaymentSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payment_type: int | str
    date_expires: str
