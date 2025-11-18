from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from api.client import KBJUApiClient
from keyboards.common import main_menu_keyboard

router = Router(name="start")


def _format_daily_stats(stats) -> str:
    return (
        f"Дата: <b>{stats.date}</b>\n"
        f"Ккал: <b>{stats.kcal:.0f}</b>\n"
        f"Белки: <b>{stats.protein:.1f}</b>\n"
        f"Жиры: <b>{stats.fat:.1f}</b>\n"
        f"Углеводы: <b>{stats.carbs:.1f}</b>"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, api_client: KBJUApiClient) -> None:
    user = message.from_user
    assert user is not None

    me = await api_client.get_me(telegram_id=user.id)

    if me is None:
        text = (
            "Привет! 👋\n\n"
            "Я бот для учёта БЖУ по штрихкодам.\n"
            "Отправь мне штрихкод продукта (как текст или фото со сканом), "
            "и я попробую найти его в базе.\n\n"
            "Профиль будет создан при первом треке продукта."
        )
    else:
        text = (
            f"С возвращением, <b>{me.profile.first_name or 'друг'}</b>!\n\n"
            "Твоя статистика на сегодня:\n"
            f"{_format_daily_stats(me.today)}"
            if me.today
            else (
                f"Привет, <b>{me.profile.first_name or 'друг'}</b>!\n\n"
                "На сегодня ещё нет записей. Скинь штрихкод, чтобы начать."
            )
        )

    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("me"))
@router.message(F.text == "📊 Мои БЖУ сегодня")
async def cmd_me(message: Message, api_client: KBJUApiClient) -> None:
    user = message.from_user
    assert user is not None

    me = await api_client.get_me(telegram_id=user.id)

    if me is None or me.today is None:
        await message.answer(
            "Пока нет данных на сегодня. Отправь штрихкод продукта, чтобы добавить приём пищи.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = "Твоя статистика на сегодня:\n" + _format_daily_stats(me.today)
    await message.answer(text, reply_markup=main_menu_keyboard())
