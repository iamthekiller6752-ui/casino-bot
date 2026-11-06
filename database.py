import aiosqlite
import time

DB = "casino.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            biggest_win INTEGER DEFAULT 0,
            last_bonus INTEGER DEFAULT 0,
            total_bets INTEGER DEFAULT 0
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
        async with db.execute("SELECT user_id, balance, wins FROM users ORDER BY balance DESC LIMIT 10") as cur:
            return await cur.fetchall()

async def claim_bonus(user_id):
    user = await get_user(user_id)
    last_bonus = user[5]
    now = int(time.time())
    if now - last_bonus < 86400:
        return False, 86400 - (now - last_bonus)
    
    # Бонус зависит от баланса (чем богаче, тем меньше бонус, чтобы не было инфляции)
    bonus = 500 if user[1] < 5000 else 250
    await change_balance(user_id, bonus)
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (now, user_id))
        await db.commit()
    return True, bonus
