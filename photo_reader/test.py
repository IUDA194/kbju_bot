import asyncio
from reader import extract_barcode_from_qr


async def main():
    barcode = await extract_barcode_from_qr("/Users/aroslavgladkij/Library/Group Containers/6N38VWS5BX.ru.keepcoder.Telegram/appstore/account-9240665789354732749/postbox/media/telegram-cloud-photo-size-2-5249139228099155078-m.jpg")

    print("Баркод:", barcode)

if __name__ == "__main__":
    asyncio.run(main())
