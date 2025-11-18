from enum import Enum

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from api.client import KBJUApiClient, NutritionResponse, TrackBarcodeResponse
from keyboards.common import (
    record_choice_keyboard,
    track_keyboard,
    main_menu_keyboard,
)

router = Router(name="barcode")


class RecordMode(str, Enum):
    GRAMS = "grams"
    SERVINGS = "servings"


class RecordStates(StatesGroup):
    waiting_for_mode = State()
    waiting_for_amount = State()


# ---------- Утилиты ----------


def _is_barcode(text: str) -> bool:
    text = text.strip()
    return text.isdigit() and len(text) >= 8


def _format_product_info(product: NutritionResponse) -> str:
    per100 = product.per_100g
    serv = product.serving

    lines = [
        f"<b>{product.name}</b>",
        f"Штрихкод: <code>{product.barcode}</code>",
        "",
        "<b>На 100 г:</b>",
        f"Ккал: {per100.kcal or '—'}; "
        f"Б: {per100.protein or '—'}; "
        f"Ж: {per100.fat or '—'}; "
        f"У: {per100.carbs or '—'}",
        "",
        "<b>За порцию:</b>",
        f"Размер порции: {serv.size or '—'}",
        f"Ккал: {serv.kcal or '—'}; "
        f"Б: {serv.protein or '—'}; "
        f"Ж: {serv.fat or '—'}; "
        f"У: {serv.carbs or '—'}",
    ]
    return "\n".join(lines)


def _format_daily_stats(resp: TrackBarcodeResponse) -> str:
    d = resp.daily
    lines = [
        f"Записал: <b>{resp.name}</b>",
        "",
        "Текущая дневная статистика:",
        f"Дата: <b>{d.date}</b>",
        f"Ккал: <b>{d.kcal:.0f}</b>",
        f"Белки: <b>{d.protein:.1f}</b>",
        f"Жиры: <b>{d.fat:.1f}</b>",
        f"Углеводы: <b>{d.carbs:.1f}</b>",
    ]
    return "\n".join(lines)


# ---------- Хендлеры ----------


@router.message(F.text.func(lambda t: t is not None and _is_barcode(t)))
async def handle_barcode_text(
    message: Message,
    state: FSMContext,
    api_client: KBJUApiClient,
) -> None:
    """Пользователь прислал штрихкод как текст."""
    assert message.text is not None
    barcode = message.text.strip()

    product = await api_client.get_bju_by_barcode(barcode)
    if product is None:
        await message.answer(
            "Не удалось найти продукт по этому штрихкоду. 😔\n"
            "Попробуй другой или проверь, правильно ли введён код.",
            reply_markup=main_menu_keyboard(),
        )
        return

    # сохраняем данные в FSM
    await state.update_data(
        barcode=product.barcode,
        product_name=product.name,
    )
    await state.set_state(RecordStates.waiting_for_mode)

    await message.answer(
        _format_product_info(product),
        reply_markup=record_choice_keyboard(),
    )


@router.callback_query(F.data == "record:grams")
async def cb_record_grams(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(record_mode=RecordMode.GRAMS.value)
    await state.set_state(RecordStates.waiting_for_amount)

    await callback.message.answer(
        "Сколько <b>грамм</b> вы съели?\n"
        "Пример: <code>120</code>",
    )
    await callback.answer()


@router.callback_query(F.data == "record:servings")
async def cb_record_servings(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(record_mode=RecordMode.SERVINGS.value)
    await state.set_state(RecordStates.waiting_for_amount)

    await callback.message.answer(
        "Сколько <b>порций</b> вы съели?\n"
        "Пример: <code>1</code> или <code>0.5</code>",
    )
    await callback.answer()


@router.message(RecordStates.waiting_for_amount, F.text)
async def handle_amount_input(
    message: Message,
    state: FSMContext,
) -> None:
    text = (message.text or "").replace(",", ".").strip()
    try:
        value = float(text)
        if value <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "Нужно ввести положительное число.\n"
            "Например: <code>100</code> или <code>0.5</code>",
        )
        return

    data = await state.get_data()
    mode_str = data.get("record_mode")
    if mode_str is None:
        await message.answer("Что-то пошло не так, попробуйте ещё раз отправить штрихкод.")
        await state.clear()
        return

    await state.update_data(amount=value)

    unit = "грамм" if mode_str == RecordMode.GRAMS.value else "порций"
    await message.answer(
        f"Ок, записать <b>{value:g} {unit}</b>.\n"
        "Нажми кнопку <b>«Трек»</b>, чтобы сохранить приём пищи.",
        reply_markup=track_keyboard(),
    )


@router.callback_query(F.data == "record:track")
async def cb_track(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: KBJUApiClient,
) -> None:
    user = callback.from_user
    assert user is not None

    data = await state.get_data()
    barcode = data.get("barcode")
    amount = data.get("amount")
    mode_str = data.get("record_mode")

    if barcode is None or amount is None or mode_str is None:
        await callback.message.answer(
            "Данные для трека потерялись. Попробуйте ещё раз отправить штрихкод.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return

    grams = None
    servings = None

    if mode_str == RecordMode.GRAMS.value:
        grams = float(amount)
    else:
        servings = float(amount)

    resp = await api_client.track_bju_by_barcode(
        barcode=barcode,
        tg_user=user,
        grams=grams,
        servings=servings,
    )

    await state.clear()

    await callback.message.answer(
        _format_daily_stats(resp),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer("Записано ✅")
