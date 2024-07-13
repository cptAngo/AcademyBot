# import sys
# sys.path.append("../")

import aiosqlite

from config import CFG


async def create_table() -> None:
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(CFG.db_name) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, user_score INTEGER)''')
        # Сохраняем изменения
        await db.commit()

async def update_quiz_index(user_id: int, index: int, score: int) -> None:
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(CFG.db_name) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, user_score) VALUES (?, ?, ?)', (user_id, index, score))
        # Сохраняем изменения
        await db.commit()

async def get_user_stat(user_id) -> tuple:
     # Подключаемся к базе данных
     async with aiosqlite.connect(CFG.db_name) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index, user_score FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results
            else:
                return (0, 0)