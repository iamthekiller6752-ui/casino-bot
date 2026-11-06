import aiosqlite
import time

DB = "casino.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        # Таблица пользователей
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            biggest_win INTEGER DEFAULT 0,
            last_bonus INTEGER DEFAULT 0,
            vip_level INTEGER DEFAULT 0,
            total_bets INTEGER DEFAULT 0,
            referrer_id INTEGER,
            boost_until INTEGER DEFAULT 0
        )""")
        # Таблица квестов (ежедневные)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            user_id INTEGER,
            quest_id TEXT,
            progress INTEGER DEFAULT 0,
            claimed INTEGER DEFAULT 0,
            date TEXT,
            PRIMARY KEY (user_id, quest_id)
        )""")
        # Таблица рефералов
        await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            referred_id INTEGER PRIMARY KEY
        )""")
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()
            return await get_user(user_id)
        return row

async def change_balance(user_id, amount):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def get_balance(user_id):
    user = await get_user(user_id)
    return user[1]

async def record_game(user_id, won, bet, prize):
    async with aiosqlite.connect(DB) as db:
        if won:
            await db.execute("UPDATE users SET wins = wins + 1, total_bets = total_bets + 1, biggest_win = MAX(biggest_win, ?) WHERE user_id = ?", (prize, user_id))
        else:
            await db.execute("UPDATE users SET losses = losses + 1, total_bets = total_bets + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_leaderboard():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10") as cur:
            return await cur.fetchall()

async def claim_bonus(user_id):
    user = await get_user(user_id)
    last_bonus = user[5]
    now = int(time.time())
    if now - last_bonus < 86400:
        return False, 86400 - (now - last_bonus)
    await change_balance(user_id, 500)
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (now, user_id))
        await db.commit()
    return True, 500