import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

from quiz_data import quiz_data
from src.db_utils import create_table, get_user_stat, update_quiz_index
from src.quiz_utils import get_question, new_quiz

# Загружаем .env файл со значением апи ключа
load_dotenv()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

API_TOKEN = os.environ["api-key"]


# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message) -> None:
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    # Запускаем новый квиз
    await new_quiz(message)


@dp.callback_query()
async def answer(callback: types.CallbackQuery) -> None:
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index, current_user_score = await get_user_stat(callback.from_user.id)

    if callback.data == "right_answer":
        # Отправляем в чат сообщение, что ответ верный и увеличиваем кол-во очков, набранных пользователем
        current_user_score += 1
        await callback.message.answer("Верно!")
    else:
        correct_option = quiz_data[current_question_index]['correct_option']
        # Отправляем в чат сообщение об ошибке с указанием верного ответа
        await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, current_user_score)

    # Проверяем достигнут ли конец квиза и выводим статистику пользователя
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        end_message = f"{current_user_score} "
        if str(current_user_score).endswith("1"):
            end_message += "очко"
        elif str(current_user_score).endswith(("1", "2", "3", "4")):
            end_message += "очка"
        else:
            end_message += "очков"
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! \nВы набрали {end_message}.")

# Запуск процесса поллинга новых апдейтов
async def main():
    # Запускаем создание таблицы базы данных
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())