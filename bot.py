import os, random, time, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

import database as db
import games as g
import keyboards as kb

BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН")
ADMIN_PASSWORD = "04172014"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class States(StatesGroup):
    exchange = State()
    admin_auth = State()
    admin_ban = State()
    admin_unban = State()
    admin_give = State()
    roulette = State()

def get_display_name(username, first_name, user_id):
    if username: return f"@{username}"
    elif first_name: return first_name
    return f"ID:{user_id}"

async def fmt_bal(uid):
    return f"{await db.get_balance(uid):,}".replace(",", " ")

# БЕЗОПАСНОЕ РЕДАКТИРОВАНИЕ (ловит ошибки)
async def safe_edit(cb: CallbackQuery, text: str, reply_markup=None):
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        pass

# --- СТАРТ (Выдает сетку внизу) ---
@dp.message(CommandStart())
async def start(message: Message):
    user = await db.get_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if user[10] == 1: # Проверка на бан
        return await message.answer("❌ Вы забанены.")
    
    bal = await fmt_bal(message.from_user.id)
    await message.answer(
        f"👑 <b>CASINO ROYAL</b> 👑\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"💰 Баланс: <b>{bal} монет</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Используй сетку внизу экрана!</i>",
        parse_mode="HTML", reply_markup=kb.bottom_grid() # ВОТ ОНА, СЕТКА
    )

# --- ОБРАБОТЧИКИ НИЖНЕЙ СЕТКИ (Текстовые) ---
@dp.message(F.text == "🎰 Играть")
async def games_menu_msg(message: Message):
    await message.answer("🎮 <b>Выбери игру:</b>", reply_markup=kb.games_menu())

@dp.message(F.text == "🛒 Магазин")
async def shop_menu_msg(message: Message):
    await message.answer("🛒 <b>МАГАЗИН</b>\n🏠 Дом — 10 000 💰\n💎 VIP — 50 000 💰", reply_markup=kb.shop_menu())

@dp.message(F.text == "👤 Профиль")
async def profile_msg(message: Message):
    u = await db.get_user(message.from_user.id)
    display_name = get_display_name(u[1], u[2], u[0])
    text = f"👤 <b>ПРОФИЛЬ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nИмя: <b>{display_name}</b>\nБаланс: <b>{await fmt_bal(u[0])} 💰</b>\nПобед: <b>{u[3]}</b> | Поражений: <b>{u[4]}</b>"
    await message.answer(text, reply_markup=kb.back_menu())

@dp.message(F.text == "🏆 Топ-10")
async def top_msg(message: Message):
    rows = await db.get_leaderboard()
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text = "🏆 <b>ТОП-10 ИГРОКОВ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    for i, row in enumerate(rows):
        uid, username, first_name, bal, wins = row
        display_name = get_display_name(username, first_name, uid)
        text += f"{medals[i]} {display_name} — <b>{bal:,} 💰</b>\n".replace(",", " ")
    await message.answer(text, reply_markup=kb.back_menu())

@dp.message(F.text == "💼 Заработок")
async def work_msg(message: Message):
    user = await db.get_user(message.from_user.id)
    if int(time.time()) - user[9] < 3600:
        return await message.answer("⏰ Ты устал. Отдохни еще час.")
    
    reward = random.randint(100, 500)
    await db.change_balance(message.from_user.id, reward)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET last_work = ? WHERE user_id = ?", (int(time.time()), message.from_user.id))
        await d.commit()
    await message.answer(f"💼 Ты заработал: <b>+{reward} 💰</b>", reply_markup=kb.back_menu())

# --- ИНЛАЙН ОБРАБОТЧИКИ ---
@dp.callback_query(F.data == "menu_main")
async def menu_main(cb: CallbackQuery):
    await cb.answer()
    bal = await fmt_bal(cb.from_user.id)
    text = f"🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n💰 Баланс: <b>{bal} 💰</b>\n\n<i>Используй сетку внизу экрана!</i>"
    await safe_edit(cb, text, kb.back_menu())

@dp.callback_query(F.data == "menu_games")
async def menu_games(cb: CallbackQuery):
    await cb.answer()
    await safe_edit(cb, "🎮 <b>ВЫБОР ИГРЫ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n<i>Нажми на игру:</i>", kb.games_menu())

# --- СТАВКИ (ИСПРАВЛЕН БАГ С ЗАГРУЗКОЙ) ---
@dp.callback_query(F.data.in_({"game_slots", "game_dice", "game_coin", "game_roulette"}))
async def choose_bet(cb: CallbackQuery):
    await cb.answer() # СРАЗУ УБИРАЕМ ЗАГРУЗКУ
    game = cb.data.replace("game_", "")
    bal = await fmt_bal(cb.from_user.id)
    await safe_edit(cb, f"💰 Баланс: <b>{bal} 💰</b>\n\nВыбери ставку:", kb.bet_menu(game))

@dp.callback_query(F.data.startswith("bet_"))
async def process_bet(cb: CallbackQuery):
    await cb.answer() # СРАЗУ УБИРАЕМ ЗАГРУЗКУ
    
    _, game, amount = cb.data.split("_")
    balance = await db.get_balance(cb.from_user.id)
    bet = balance if amount == "all" else int(amount)
    
    if bet <= 0 or bet > balance:
        return await cb.answer("❌ Недостаточно средств!", show_alert=True)

    if game == "slots":
        await play_slots(cb, bet)
    elif game == "dice":
        await safe_edit(cb, f"🎲 Ставка: <b>{bet} 💰</b>\nНа что ставишь?", kb.dice_choice(bet))
    elif game == "coin":
        await safe_edit(cb, f"🪙 Ставка: <b>{bet} 💰</b>\nОрёл или решка?", kb.coin_choice(bet))
    elif game == "roulette":
        await safe_edit(cb, f"🎡 Ставка: <b>{bet} 💰</b>\nВыбери сектор:", kb.roulette_choice(bet))

# --- СЛОТЫ ---
async def play_slots(cb, bet):
    await db.change_balance(cb.from_user.id, -bet)
    reels = g.spin_slots()
    mult = g.slots_multiplier(reels)
    prize = int(bet * mult)
    if prize: await db.change_balance(cb.from_user.id, prize)
    await db.record_game(cb.from_user.id, prize > 0, bet, prize)

    net = prize - bet
    res = f"🟢 <b>+{net} 💰</b>" if net >= 0 else f"🔴 <b>{net} 💰</b>"
    bal = await fmt_bal(cb.from_user.id)
    text = f"🎰 <b>СЛОТЫ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n| {reels[0]} | {reels[1]} | {reels[2]} |\n➖➖➖➖➖➖➖➖➖➖➖➖\nСтавка: <b>{bet} 💰</b>\nВыигрыш: {res}\n💰 Баланс: <b>{bal} 💰</b>"
    await safe_edit(cb, text, kb.after_game("slots"))

# --- КОСТИ ---
@dp.callback_query(F.data.startswith("dice_"))
async def play_dice(cb: CallbackQuery):
    await cb.answer()
    _, choice, bet = cb.data.split("_")
    bet = int(bet)
    if bet > await db.get_balance(cb.from_user.id):
        return await cb.answer("❌ Мало монет", show_alert=True)

    await db.change_balance(cb.from_user.id, -bet)
    roll = g.roll_dice()
    won, mult = False, 0
    if choice == "over" and roll > 3: won, mult = True, 1.9
    elif choice == "under" and roll < 4: won, mult = True, 1.9
    elif choice == "six" and roll == 6: won, mult = True, 5
    elif choice == "one" and roll == 1: won, mult = True, 5

    prize = int(bet * mult) if won else 0
    if prize: await db.change_balance(cb.from_user.id, prize)
    await db.record_game(cb.from_user.id, won, bet, prize)

    net = prize - bet
    res = f"🟢 <b>+{net} 💰</b>" if net >= 0 else f"🔴 <b>{net} 💰</b>"
    bal = await fmt_bal(cb.from_user.id)
    text = f"🎲 <b>КОСТИ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nВыпало: {g.DICE_EMOJI[roll-1]} <b>{roll}</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nСтавка: <b>{bet} 💰</b>\nВыигрыш: {res}\n💰 Баланс: <b>{bal} 💰</b>"
    await safe_edit(cb, text, kb.after_game("dice"))

# --- МОНЕТКА ---
@dp.callback_query(F.data.startswith("coin_"))
async def play_coin(cb: CallbackQuery):
    await cb.answer()
    _, choice, bet = cb.data.split("_")
    bet = int(bet)
    if bet > await db.get_balance(cb.from_user.id):
        return await cb.answer("❌ Мало монет", show_alert=True)

    await db.change_balance(cb.from_user.id, -bet)
    result = g.flip_coin()
    won = result == choice
    prize = bet * 2 if won else 0
    if prize: await db.change_balance(cb.from_user.id, prize)
    await db.record_game(cb.from_user.id, won, bet, prize)

    emoji, name = ("🪙", "Орёл") if result == "heads" else ("🦅", "Решка")
    net = prize - bet
    res = f"🟢 <b>+{net} 💰</b>" if net >= 0 else f"🔴 <b>{net} 💰</b>"
    bal = await fmt_bal(cb.from_user.id)
    text = f"🪙 <b>МОНЕТКА</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nВыпало: {emoji} <b>{name}</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nСтавка: <b>{bet} 💰</b>\nВыигрыш: {res}\n💰 Баланс: <b>{bal} 💰</b>"
    await safe_edit(cb, text, kb.after_game("coin"))

# --- РУЛЕТКА ---
@dp.callback_query(F.data.startswith("roul_"))
async def play_roulette(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    parts = cb.data.split("_")
    
    if parts[1] == "num":
        bet = int(parts[2])
        await state.update_data(bet=bet)
        await state.set_state(States.roulette)
        return await safe_edit(cb, f"🎯 Ставка <b>{bet} 💰</b>\nОтправь число от 0 до 36:", kb.back_menu())

    choice, bet = parts[1], int(parts[2])
    if bet > await db.get_balance(cb.from_user.id):
        return await cb.answer("❌ Мало монет", show_alert=True)

    await db.change_balance(cb.from_user.id, -bet)
    num = g.spin_roulette()
    color = g.roulette_color(num)
    won, mult = False, 0
    if choice == "red" and color == "red": won, mult = True, 2
    elif choice == "black" and color == "black": won, mult = True, 2
    elif choice == "green" and color == "green": won, mult = True, 14

    prize = int(bet * mult) if won else 0
    if prize: await db.change_balance(cb.from_user.id, prize)
    await db.record_game(cb.from_user.id, won, bet, prize)

    color_emoji = {"red":"🔴","black":"⚫","green":"🟢"}[color]
    net = prize - bet
    res = f"🟢 <b>+{net} 💰</b>" if net >= 0 else f"🔴 <b>{net} 💰</b>"
    bal = await fmt_bal(cb.from_user.id)
    text = f"🎡 <b>РУЛЕТКА</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nВыпало: {color_emoji} <b>{num}</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nСтавка: <b>{bet} 💰</b>\nВыигрыш: {res}\n💰 Баланс: <b>{bal} 💰</b>"
    await safe_edit(cb, text, kb.after_game("roulette"))

@dp.message(States.roulette)
async def roulette_number(message: Message, state: FSMContext):
    try:
        num = int(message.text)
        if not 0 <= num <= 36: raise ValueError
    except: return await message.answer("❌ Введи число от 0 до 36")
    
    data = await state.get_data()
    bet = data["bet"]
    await state.clear()

    if bet > await db.get_balance(message.from_user.id):
        return await message.answer("❌ Недостаточно средств", reply_markup=kb.bottom_grid())

    await db.change_balance(message.from_user.id, -bet)
    result = g.spin_roulette()
    won = result == num
    prize = bet * 36 if won else 0
    if prize: await db.change_balance(message.from_user.id, prize)
    await db.record_game(message.from_user.id, won, bet, prize)

    color = g.roulette_color(result)
    emoji = {"red":"🔴","black":"⚫","green":"🟢"}[color]
    net = prize - bet
    res = f"🟢 <b>+{net} 💰</b>" if net >= 0 else f"🔴 <b>{net} 💰</b>"
    bal = await fmt_bal(message.from_user.id)
    text = f"🎯 <b>РУЛЕТКА (Число)</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nВыпало: {emoji} <b>{result}</b> (твоё: {num})\n➖➖➖➖➖➖➖➖➖➖➖➖\nВыигрыш: {res}\n💰 Баланс: <b>{bal} 💰</b>"
    await message.answer(text, reply_markup=kb.bottom_grid())

# --- АДМИНКА ---
@dp.message(Command("adminpanelss"))
async def admin_start(message: Message, state: FSMContext):
    await message.answer("🔐 Введите пароль:")
    await state.set_state(States.admin_auth)

@dp.message(States.admin_auth)
async def admin_auth(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.clear()
        await message.answer("👑 <b>АДМИН-ПАНЕЛЬ</b>", parse_mode="HTML", reply_markup=kb.admin_menu())
    else:
        await message.answer("❌ Неверный пароль.")
        await state.clear()

@dp.callback_query(F.data.startswith("admin_"))
async def admin_actions(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    action = cb.data.split("_")[1]
    if action == "ban":
        await safe_edit(cb, "Введите ID игрока для бана:", kb.back_menu())
        await state.set_state(States.admin_ban)
    elif action == "unban":
        await safe_edit(cb, "Введите ID игрока для разбана:", kb.back_menu())
        await state.set_state(States.admin_unban)
    elif action == "give":
        await safe_edit(cb, "Введите `ID Сумма` для выдачи:", kb.back_menu())
        await state.set_state(States.admin_give)

@dp.message(States.admin_ban)
async def process_ban(message: Message, state: FSMContext):
    try:
        target_id = int(message.text)
        async with db.aiosqlite.connect(db.DB) as d:
            await d.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (target_id,))
            await d.commit()
        await message.answer(f"✅ Игрок {target_id} забанен.", reply_markup=kb.admin_menu())
    except: await message.answer("❌ Ошибка ID.", reply_markup=kb.admin_menu())
    await state.clear()

@dp.message(States.admin_unban)
async def process_unban(message: Message, state: FSMContext):
    try:
        target_id = int(message.text)
        async with db.aiosqlite.connect(db.DB) as d:
            await d.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (target_id,))
            await d.commit()
        await message.answer(f"✅ Игрок {target_id} разбанен.", reply_markup=kb.admin_menu())
    except: await message.answer("❌ Ошибка ID.", reply_markup=kb.admin_menu())
    await state.clear()

@dp.message(States.admin_give)
async def process_give(message: Message, state: FSMContext):
    try:
        target_id, amount = map(int, message.text.split())
        await db.change_balance(target_id, amount)
        await message.answer(f"✅ Выдано {amount} 💰.", reply_markup=kb.admin_menu())
    except: await message.answer("❌ Формат: ID Сумма", reply_markup=kb.admin_menu())
    await state.clear()
