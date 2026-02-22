from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration, Payment
import logging
from core import db_helper
from core.auth.crud import get_current_user
from core.payments.manager import (
    create_payment,
    payment_find,
    payment_cancel,
    partial_debiting,
    create_payment_with_future_linking_card_during_payment,
    check_payment_linking_card_during_payment,
    payment_with_linked_card,
    create_invoice,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/add")
async def create(
    price: int,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await create_payment(price, request=request, session=session)


@router.get("/get")
async def get_payments():
    return Payment.list()


@router.post("/invoice/add")
async def invoice():
    return await create_invoice()


@router.post("/add/payment/future/linking")
async def create_with_linking(
    request: Request,
    price: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    """
    Совершить платеж, с согласием на привязку карты, дальнейшие платежи можно совершать без указания карты,
    payment_method_id брать с БД конкретного юзера
    МЕТОД РАБОТАЕТ ТОЛЬКО С БАНКОВСКИМИ КАРТАМИ
    """
    return await create_payment_with_future_linking_card_during_payment(
        amount=price, request=request, session=session
    )


@router.post("/add/with/linking")
async def linked_payment(
    amount: int,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await payment_with_linked_card(
        amount=amount,
        request=request,
        session=session,
    )


@router.get("/check/with/linking")
def check_with_linking(payment_id):
    return check_payment_linking_card_during_payment(payment_id)


@router.get("/find")
def find_by_id(payment_id):
    return payment_find(payment_id)


@router.post("/add/partial")
def create_partial_debiting(payment_id):
    return partial_debiting(payment_id)


@router.delete("/delete")
def cancel(payment_id):
    return payment_cancel(payment_id)
