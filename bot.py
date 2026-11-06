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
    blackjack = State()
    roulette = State()

def get_display_name(username, first_name, user_id):
    if username: return f"@{username}"
    elif first_name: return first_name
    return f"ID:{user_id}"

async def fmt_bal(uid):
    return f"{await db.get_balance(uid):,}".replace(",", " ")

# ФУНКЦИЯ БЕЗОПАСНОГО РЕДАКТИРОВАНИЯ (лечит бесконечную загрузку)
async def safe_edit(cb: CallbackQuery, text: str, reply_markup=None):
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        pass # Игнорируем ошибку, если текст не изменился
    await cb.answer() # ВСЕГДА убираем загрузку

@dp.message(CommandStart())
async def start(message: Message):
    user = await db.get_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if user[12] == 1:
        return await message.answer("❌ Вы забанены.")
    
    bal = await fmt_bal(message.from_user.id)
    await message.answer(
        f"👑 <b>CASINO ROYAL</b> 👑\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"💰 Баланс: <b>{bal} монет</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Выбирай действия на кнопках ниже:</i>",
        parse_mode="HTML", reply_markup=kb.main_menu()
    )

@dp.callback_query(F.data == "menu_main")
async def menu_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    bal = await fmt_bal(cb.from_user.id)
    text = f"🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n💰 Баланс: <b>{bal} 💰</b>"
    await safe_edit(cb, text, kb.main_menu())

# --- ИГРЫ ---
@dp.callback_query(F.data == "menu_games")
async def menu_games(cb: CallbackQuery):
    await safe_edit(cb, "🎮 <b>ВЫБОР ИГРЫ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n<i>Нажми на игру:</i>", kb.games_menu())

@dp.callback_query(F.data.in_({"game_slots", "game_dice", "game_coin", "game_roulette"}))
async def choose_bet(cb: CallbackQuery):
    game = cb.data.replace("game_", "")
    bal = await fmt_bal(cb.from_user.id)
    await safe_edit(cb, f"💰 Баланс: <b>{bal} 💰</b>\n\nВыбери ставку:", kb.bet_menu(game))

@dp.callback_query(F.data.startswith("bet_"))
async def process_bet(cb: CallbackQuery):
    _, game, amount = cb.data.split("_")
    
    # СРАЗУ убираем загрузку кнопки, чтобы не было бесконечного кружочка
    await cb.answer() 
    
    balance = await db.get_balance(cb.from_user.id)
    bet = balance if amount == "all" else int(amount)
    
    if bet <= 0 or bet > balance:
        return await cb.answer("❌ Недостаточно средств!", show_alert=True)

    if game == "slots":
        await play_slots(cb, bet)
    elif game == "dice":
        await cb.message.edit_text(f"🎲 Ставка: <b>{bet} 💰</b>\nНа что ставишь?", reply_markup=kb.dice_choice(bet))
    elif game == "coin":
        await cb.message.edit_text(f"🪙 Ставка: <b>{bet} 💰</b>\nОрёл или решка?", reply_markup=kb.coin_choice(bet))
    elif game == "roulette":
        await cb.message.edit_text(f"🎡 Ставка: <b>{bet} 💰</b>\nВыбери сектор:", reply_markup=kb.roulette_choice(bet))

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
    _, choice, bet = cb.data.split("_")
    bet = int(bet)
    await cb.answer()
    
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
    _, choice, bet = cb.data.split("_")
    bet = int(bet)
    await cb.answer()
    
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
    parts = cb.data.split("_")
    await cb.answer()
    
    if parts[1] == "num":
        bet = int(parts[2])
        await state.update_data(bet=bet)
        await state.set_state(States.roulette)
        return await cb.message.edit_text(f"🎯 Ставка <b>{bet} 💰</b>\nОтправь число от 0 до 36:", reply_markup=kb.back_menu())

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
        return await message.answer("❌ Недостаточно средств", reply_markup=kb.main_menu())

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
    await message.answer(text, reply_markup=kb.main_menu())

# --- ЛИДЕРБОРД (ИСПРАВЛЕНО НА ЮЗЕРНЕЙМЫ) ---
@dp.callback_query(F.data == "menu_top")
async def top(cb: CallbackQuery):
    rows = await db.get_leaderboard()
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text = "🏆 <b>ТОП-10 ИГРОКОВ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    
    for i, row in enumerate(rows):
        uid, username, first_name, bal, wins = row
        display_name = get_display_name(username, first_name, uid)
        text += f"{medals[i]} {display_name} — <b>{bal:,} 💰</b>\n".replace(",", " ")
        
    await safe_edit(cb, text, kb.back_menu())

# --- РАБОТА / МАГАЗИН / ПРОФИЛЬ ---
@dp.callback_query(F.data == "menu_work")
async def work_menu(cb: CallbackQuery):
    await cb.answer()
    user = await db.get_user(cb.from_user.id)
    if int(time.time()) - user[11] < 3600:
        return await cb.answer("⏰ Ты устал. Отдохни еще час.", show_alert=True)
    
    reward = random.randint(100, 500)
    await db.change_balance(cb.from_user.id, reward)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET last_work = ? WHERE user_id = ?", (int(time.time()), cb.from_user.id))
        await d.commit()
    await safe_edit(cb, f"💼 Ты заработал: <b>+{reward} 💰</b>", kb.back_menu())

@dp.callback_query(F.data == "menu_shop")
async def shop(cb: CallbackQuery):
    text = f"🛒 <b>МАГАЗИН</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n🏠 Дом — 10 000 💰\n💎 VIP — 50 000 💰"
    await safe_edit(cb, text, kb.shop_menu())

@dp.callback_query(F.data == "shop_buy_house")
async def buy_house(cb: CallbackQuery):
    await cb.answer()
    if await db.get_balance(cb.from_user.id) < 10000: return await cb.answer("❌ Мало денег!", show_alert=True)
    await db.change_balance(cb.from_user.id, -10000)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET house_id = 1 WHERE user_id = ?", (cb.from_user.id,))
        await d.commit()
    await cb.answer("✅ Дом куплен!", show_alert=True)

@dp.callback_query(F.data == "menu_profile")
async def profile(cb: CallbackQuery):
    u = await db.get_user(cb.from_user.id)
    display_name = get_display_name(u[1], u[2], u[0])
    text = f"👤 <b>ПРОФИЛЬ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\nИмя: <b>{display_name}</b>\nБаланс: <b>{await fmt_bal(u[0])} 💰</b>\nПобед: <b>{u[4]}</b> | Поражений: <b>{u[5]}</b>"
    await safe_edit(cb, text, kb.back_menu())

@dp.callback_query(F.data == "menu_exchange")
async def exchange_start(cb: CallbackQuery, state: FSMContext):
    await safe_edit(cb, "🔄 <b>ОБМЕННИК</b>\nНапиши <b>@ник</b> и сумму:\nПример: <code>@durov 500</code>", kb.back_menu())
    await state.set_state(States.exchange)

@dp.message(States.exchange)
async def exchange_process(message: Message, state: FSMContext):
    try:
        target_str, amount_str = message.text.split()
        amount = int(amount_str)
        if amount <= 0: raise ValueError
    except:
        return await message.answer("❌ Формат: @ник Сумма")
    
    target_id = await db.get_user_by_username(target_str[1:]) if target_str.startswith("@") else int(target_str)
    if not target_id: return await message.answer("❌ Игрок не найден.")
    if target_id == message.from_user.id: return await message.answer("❌ Нельзя себе.")
    if await db.get_balance(message.from_user.id) < amount: return await message.answer("❌ Мало денег.")
    
    await db.change_balance(message.from_user.id, -amount)
    await db.change_balance(target_id, amount)
    await message.answer(f"✅ Переведено <b>{amount} 💰</b> игроку {target_str}", reply_markup=kb.main_menu())
    await state.clear()
