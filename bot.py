import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from states import SearchStates
from parser import parse_doski
from keyboards import start_keyboard


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет! Нажми 'Начать', чтобы выполнить поиск на doski.ru",
        reply_markup=start_keyboard
    )


@dp.message(F.text == "Начать")
async def begin_search(message: Message, state: FSMContext):
    await message.answer("Что будем искать?")
    await state.set_state(SearchStates.waiting_for_query)


@dp.message(SearchStates.waiting_for_query)
async def get_query(message: Message, state: FSMContext):
    await state.update_data(query=message.text)
    await message.answer("Минимальная цена? (или 0)")
    await state.set_state(SearchStates.waiting_for_min_price)


@dp.message(SearchStates.waiting_for_min_price)
async def get_min_price(message: Message, state: FSMContext):
    min_price = message.text
    await state.update_data(min_price=min_price)
    await message.answer("Максимальная цена? (или 0)")
    await state.set_state(SearchStates.waiting_for_max_price)


@dp.message(SearchStates.waiting_for_max_price)
async def get_max_price(message: Message, state: FSMContext):
    max_price = message.text
    await state.update_data(max_price=max_price)

    data = await state.get_data()

    query = data.get("query")
    min_price = data.get("min_price")
    max_price = data.get("max_price")

    await message.answer("Выполняю поиск...")

    results = parse_doski(
        query=query,
        min_price=None if min_price == "0" else min_price,
        max_price=None if max_price == "0" else max_price
    )

    if results:
        text = "Вот что удалось найти:\n\n"
        for link in results:
            text += link + "\n\n"
    else:
        text = "Ничего не найдено."

    await message.answer(text)
    await state.clear()


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
