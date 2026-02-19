import uuid
from datetime import datetime

from fastapi import HTTPException, status, Depends, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from yookassa import Configuration, Payment
import os
from dotenv import load_dotenv
from yookassa.domain.exceptions import NotFoundError

from dotenv import load_dotenv

from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.models.payments import Payments
from core.schemas.payments import PaymentSchema

load_dotenv()
Configuration.account_id = os.getenv("YOOKASSA__ACCOUNT__ID")
Configuration.secret_key = os.getenv("YOOKASSA__SECRET__KEY")


def payment_cancel(payment):
    Payment.cancel(payment)


def payment_find(payment):
    data = Payment.find_one(payment)
    return data
    # try:
    #     if data:
    #         if data["payment_method"]["type"] == "card":
    #             return PaymentSchema(
    #                 payment_type=data["payment_method"]["type"],
    #                 date_expires=f'{data["payment_method"]["card"]["expiry_year"]} year, {data["payment_method"]["card"]["expiry_month"]} month',
    #             )
    #         elif data["payment_method"]["type"] == "yoo_money":
    #             return PaymentSchema(
    #                 payment_type=data["payment_method"]["type"],
    #                 date_expires=data["payment_method"]["title"],
    #             )
    # except NotFoundError:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Идентификатор платежа указан не верно",
    #     )


async def create_payment_with_future_linking_card_during_payment(
    request: Request,
    amount: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(request=request, session=session)
    data = await run_in_threadpool(
        Payment.create,
        {
            "amount": {"value": amount, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"http://localhost:5173/games",
            },
            "capture": True,
            "description": "Заказ №1",
            # """
            #  Если save_payment_method = False, или не указан
            #  - payment_method_id не вернется (нужен для оплаты без указания карты)
            # """
            "save_payment_method": True,
        },
        idempotency_key=uuid.uuid4(),
    )
    created_at = datetime.fromisoformat(data.created_at.replace("Z", "+00:00"))
    stmt = Payments(
        payment_id=data.id,
        user_id=user["user_id"],
        price=data.amount.value,
        description=data.description,
        status=data.status,
        created_at=created_at,
    )
    session.add(stmt)
    await session.commit()

    return data


async def payment_with_linked_card(
    request: Request,
    amount: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(request=request, session=session)
    stmt = select(Payments.payment_method_id).where(
        and_(Payments.user_id == user["user_id"], Payments.payment_for_linking == True)
    )
    res = await session.execute(stmt)
    payment_method_id = res.scalar()

    data = await run_in_threadpool(
        Payment.create,
        {
            "amount": {"value": amount, "currency": "RUB"},
            "payment_method_id": payment_method_id,  # ID сохранённой карты
            "description": "Платеж без указания карты",
        },
        idempotency_key=uuid.uuid4(),
    )

    return data


def check_payment_linking_card_during_payment(payment_id):
    try:
        data = Payment.find_one(payment_id)
        if data["status"] == "succeeded" and data["payment_method"]["saved"]:
            # return "Платеж обработан успешно и привязка создана"
            # return data["payment_method"]["id"]
            return data
        elif data["status"] == "pending":
            return "Платеж в обработке"

        elif data["status"] == "waiting_for_capture":
            return "Платеж ожидает подтверждения"
        else:
            return "Привязка еще не создана"

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Идентификатор платежа указан не верно",
        )


async def create_payment(
    price,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(session, request)
    payment = await run_in_threadpool(
        Payment.create,
        {
            "amount": {"value": price, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"http://localhost:5173/games",
            },
            "capture": True,
            "description": "Заказ №1",
        },
        idempotency_key=uuid.uuid4(),
    )
    created_at = datetime.fromisoformat(payment.created_at.replace("Z", "+00:00"))
    stmt = Payments(
        payment_id=payment.id,
        user_id=user.get("user_id"),
        price=price,
        description=payment.description,
        status=payment.status,
        created_at=created_at,
    )
    session.add(stmt)
    await session.commit()

    return payment


def partial_debiting(payment_id):
    payment = Payment.capture(
        payment_id,
        {
            "amount": {
                "value": 5,
                "currency": "RUB",
            },  # в бд надо будет искать value по payment_id
        },
    )
    return payment
