import json

from fastapi import APIRouter, Depends, Request
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete
from yookassa import Configuration, Webhook
from yookassa.domain.notification import WebhookNotification

from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.models.payments import Payments

log = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Webhooks"])


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    """Доработать обработку - yoomoney или bank_card приходит, там тело другое"""
    try:
        event_json = await request.json()
        log.info(f"Получен webhook: {event_json}")

        notification = WebhookNotification(event_json)
        payment = notification.object
        event_type = notification.event
        if payment.payment_method.type == "yoo_money":
            if event_type == "payment.succeeded":
                await session.execute(
                    update(Payments)
                    .where(Payments.payment_id == payment.id)
                    .values(
                        status=payment.status,
                        payment_method_id=payment.payment_method.id,
                        type=payment.payment_method.type,
                        payment_details=payment.payment_method.__dict__,
                    )
                )
                await session.commit()
        elif payment.payment_method.type == "bank_card":
            if payment.payment_method.saved:
                log.info(f"SAVED VALUE FROM WEBHOOK: {payment.payment_method.saved}")
                payment_details = json.loads(payment.payment_method.json())
                await session.execute(
                    update(Payments)
                    .where(Payments.payment_id == payment.id)
                    .values(
                        payment_details=payment_details,
                        payment_method_id=payment.payment_method.id,
                        type=payment.payment_method.type,
                        status=payment.status,
                        payment_for_linking=True,
                    )
                )
                await session.commit()
            else:
                payment_details = json.loads(payment.payment_method.json())
                log.info(f"SAVED VALUE FROM WEBHOOK: {payment.payment_method.saved}")
                await session.execute(
                    update(Payments)
                    .where(Payments.payment_id == payment.id)
                    .values(
                        payment_details=payment_details,
                        payment_method_id=payment.payment_method.id,
                        type=payment.payment_method.type,
                        status=payment.status,
                        payment_for_linking=False,
                    )
                )
                await session.commit()
    except Exception as e:
        log.error(f"Ошибка обработки webhook: {e}")
        return {"status": "error", "message": str(e)}


# payment_id=payment.id,
#         user_id=user.get("user_id"),
#         price=price,
#         description=payment.description,
#         status=payment.status,
#         created_at=created_at,
# payment_type=None,
# payment_method_id="yoo_money",
# payment_details
