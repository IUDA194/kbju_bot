import asyncio
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from api.client import KBJUApiClient
from keyboards.common import record_choice_keyboard
from handlers.barcode import (
    _format_product_info,
    RecordStates,
)
from photo_reader.reader import extract_barcode_from_qr, QRDecodeError

router = Router(name="barcode_photo")


@router.message(F.photo)
async def handle_barcode_photo(
    message: Message,
    state: FSMContext,
    api_client: KBJUApiClient,
):
    """
    Обработка фото с QR/barcode.
    """

    user = message.from_user
    assert user is not None

    # Берём самое большое фото (последний объект)
    photo = message.photo[-1]

    # Временный путь
    tmp_path = Path(f"/tmp/{photo.file_unique_id}.jpg")
    await message.bot.download(photo, destination=tmp_path)

    try:
        barcode = await extract_barcode_from_qr(tmp_path)
    except QRDecodeError as e:
        await message.answer(f"❌ Не удалось извлечь штрихкод из фото.\n{e}")
        return
    finally:
        # Чистим файл
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    # ——— Нашли штрихкод, работаем как обычный текстовый input ———
    product = await api_client.get_bju_by_barcode(barcode)

    if product is None:
        await message.answer(
            f"❌ Не удалось найти продукт по штрихкоду <code>{barcode}</code>."
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
