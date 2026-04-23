import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Union, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from config import BOT_TOKEN
    from states import SearchStates
    from parser import parse_doski
    from keyboards import start_keyboard
except ImportError:
    BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("DoskiBotService")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())



@dp.message(CommandStart())
async def start_handler(message: Message):
    current_user = message.from_user.full_name
    log_info = f"Инициализация сессии для пользователя: {current_user}"
    print(f"[{datetime.now()}] {log_info}")
    
    welcome_payload = (
        f"Приветствуем, {current_user}!\n\n"
        "Данный программный комплекс предназначен для мониторинга "
        "объявлений на ресурсе doski.ru в режиме реального времени.\n"
        "Для активации алгоритма поиска используйте кнопку управления ниже."
    )
    
    await message.answer(
        text=welcome_payload,
        reply_markup=start_keyboard
    )

@dp.message(Command("cancel"))
@dp.message(F.text.lower() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
 
    current_active_state = await state.get_state()
    
    if current_active_state is None:
        await message.answer("В данный момент нет активных процессов для отмены.")
        return

    print(f"[{datetime.now()}] Сброс состояния для ID {message.from_user.id}")
    await state.clear()
    await message.answer(
        "Все активные задачи аннулированы. Система возвращена в исходное состояние.",
        reply_markup=start_keyboard
    )

@dp.message(F.text == "Начать")
async def begin_search(message: Message, state: FSMContext):

    prompt_text = (
        "Система готова к приему данных.\n\n"
        "Пожалуйста, введите текстовый запрос для поиска "
        "(например: оборудование, электроника, транспорт)."
    )
    
    await message.answer(
        text=prompt_text,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SearchStates.waiting_for_query)

@dp.message(SearchStates.waiting_for_query)
async def get_query(message: Message, state: FSMContext):
    """
    Валидация и сохранение поискового запроса в контекст текущей сессии.
    Выполняет проверку длины входной строки.
    """
    user_input = message.text.strip()
    
    if len(user_input) < 2:
        await message.answer("Ошибка: Запрос слишком короткий. Введите минимум 2 символа.")
        return

    await state.update_data(query=user_input)
    print(f"[{datetime.now()}] Запрос принят: {user_input}")
    
    await message.answer(
        "Запрос зафиксирован.\n"

"Укажите МИНИМАЛЬНУЮ стоимость товара в цифровом формате.\n"
        "Если нижний порог не требуется, отправьте '0'."
    )
    await state.set_state(SearchStates.waiting_for_min_price)

@dp.message(SearchStates.waiting_for_min_price)
async def get_min_price(message: Message, state: FSMContext):
    """
    Обработка числового значения минимальной цены.
    Включает блок проверки типа данных (Integer Validation).
    """
    input_data = message.text.strip()

    if not input_data.isdigit():
        await message.answer("Некорректный ввод. Система ожидает целое положительное число.")
        return

    await state.update_data(min_price=input_data)
    await message.answer(
        "Значение сохранено.\n"
        "Укажите МАКСИМАЛЬНУЮ стоимость для фильтрации.\n"
        "Или отправьте '0' для поиска без ограничений сверху."
    )
    await state.set_state(SearchStates.waiting_for_max_price)

@dp.message(SearchStates.waiting_for_max_price)
async def get_max_price(message: Message, state: FSMContext):
    """
    Финальный этап сбора данных, десериализация состояния и запуск парсера.
    Реализует логику ветвления в зависимости от полученных результатов.
    """
    input_data = message.text.strip()

    if not input_data.isdigit():
        await message.answer("Ошибка формата. Пожалуйста, используйте только цифры.")
        return

    await state.update_data(max_price=input_data)
    
    """ Извлечение агрегированных данных из хранилища FSM """
    storage_data = await state.get_data()
    
    target_query = storage_data.get("query")
    p_min = storage_data.get("min_price")
    p_max = storage_data.get("max_price")

    await message.answer("Инициирован процесс подключения к серверу... Ожидайте.")

    try:
        """ 
        Вызов внешней функции парсинга. 
        Логика преобразования строковых '0' в тип None для совместимости с API.
        """
        search_results = parse_doski(
            query=target_query,
            city="Все регионы",
            min_price=None if p_min == "0" else p_min,
            max_price=None if p_max == "0" else p_max
        )

        if search_results:
            summary_report = f"Анализ завершен. Найдено совпадений: {len(search_results)}\n\n"
            content_body = ""
            for index, url in enumerate(search_results, 1):
                content_body += f"{index}. {url}\n\n"
            
            final_message = summary_report + content_body
        else:
            final_message = "Поиск завершен: совпадений с заданными фильтрами не обнаружено."

        await message.answer(text=final_message)

    except Exception as critical_error:
        print(f"[{datetime.now()}] Ошибка исполнения: {critical_error}")
        await message.answer("Произошел внутренний программный сбой при обработке запроса.")

    await state.clear()
    await message.answer("Система готова к новому циклу поиска.", reply_markup=start_keyboard)

async def run_application_loop():
   
    print(f"[{datetime.now()}] СИСТЕМА ЗАПУЩЕНА В РЕЖИМЕ POLLING")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as runtime_exception:
        print(f"Критическая ошибка цикла: {runtime_exception}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_application_loop())
    except KeyboardInterrupt:
        print("Программа принудительно остановлена пользователем.")
