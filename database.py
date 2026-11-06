import aiosqlite
import time

DB = "casino.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        # Создаем базовую таблицу
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            biggest_win INTEGER DEFAULT 0,
            last_bonus INTEGER DEFAULT 0,
            total_bets INTEGER DEFAULT 0,
            vip_level INTEGER DEFAULT 0,
            house_id INTEGER DEFAULT 0,
            last_work INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            last_seen INTEGER DEFAULT 0
        )""")
        
        # АВТО-МИГРАЦИЯ: Добавляем новые колонки, если их нет
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in await cursor.fetchall()]
        if "username" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN username TEXT")
        if "first_name" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
        
        await db.commit()

async def get_user(user_id, username=None, first_name=None):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await db.execute("INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)", (user_id, username, first_name))
            await db.commit()
            return await get_user(user_id, username, first_name)
        
        await db.execute("UPDATE users SET username = ?, first_name = ?, last_seen = ? WHERE user_id = ?", (username, first_name, int(time.time()), user_id))
        await db.commit()
        
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            return await cur.fetchone()

async def get_balance(user_id):
    user = await get_user(user_id)
    return user[1] # В старой базе баланс на индексе 1, если миграция не сдвинула. 
    # НО: так как мы добавили колонки в конец, баланс остается на индексе 1 (если таблица создана давно).
    # Если таблица новая - баланс тоже на 1.

async def change_balance(user_id, amount):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def record_game(user_id, won, bet, prize):
    async with aiosqlite.connect(DB) as db:
        if won:
            await db.execute("UPDATE users SET wins = wins + 1, total_bets = total_bets + 1, biggest_win = MAX(biggest_win, ?) WHERE user_id = ?", (prize, user_id))
        else:
            await db.execute("UPDATE users SET losses = losses + 1, total_bets = total_bets + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_leaderboard():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT user_id, username, first_name, balance, wins FROM users WHERE banned = 0 ORDER BY balance DESC LIMIT 10") as cur:
            return await cur.fetchall()

async def get_user_by_username(username):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT user_id FROM users WHERE username = ?", (username,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None
