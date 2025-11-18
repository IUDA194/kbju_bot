import asyncio
import re
from pathlib import Path

from PIL import Image
from pyzbar.pyzbar import decode as decode_zbar


class QRDecodeError(Exception):
    """Ошибка декодирования QR-кода."""


async def extract_barcode_from_qr(image_path: str | Path) -> str:
    """
    Асинхронно достаёт цифры (баркод) из QR-кода на изображении.

    :param image_path: путь до файла с картинкой (PNG/JPEG и т.п.)
    :return: строка с цифрами (первый найденный числовой блок)
    :raises QRDecodeError: если QR не найден или цифр нет
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _sync_extract_barcode_from_qr,
        Path(image_path),
    )


def _sync_extract_barcode_from_qr(path: Path) -> str:
    if not path.exists():
        raise QRDecodeError(f"Файл не найден: {path}")

    img = Image.open(path)
    decoded = decode_zbar(img)

    if not decoded:
        raise QRDecodeError("QR-код не найден на изображении")

    # Берём первый найденный QR
    data_bytes = decoded[0].data
    data = data_bytes.decode("utf-8", errors="ignore")

    # Ищем последовательность цифр
    m = re.search(r"\d+", data)
    if not m:
        raise QRDecodeError(f"В QR нет цифр. Декодированные данные: {data!r}")

    return m.group(0)
