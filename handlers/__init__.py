from aiogram import Dispatcher

from .start import router as start_router
from .barcode import router as barcode_router
from .barcode_photo import router as barcode_photo_router
from api.client import KBJUApiClient


def register_handlers(dp: Dispatcher, api_client: KBJUApiClient) -> None:
    dp.include_router(start_router)
    dp.include_router(barcode_router)
    dp.include_router(barcode_photo_router)
