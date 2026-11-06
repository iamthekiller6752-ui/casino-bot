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

BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_ЕСЛИ_НУЖНО")
ADMIN_ID = 123456789  # Замени на свой ID!

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Blackjack(StatesGroup):
    playing = State()

class RouletteState(StatesGroup):
    waiting_number = State()

# --- КРАСИВЫЙ ХЕЛПЕР ---
async def get_fmt_bal(uid):
    bal = await db.get_balance(uid)
    return f"{bal:,}".replace(",", " ")

# --- СТАРТ ---
@dp.message(CommandStart())
async def start(message: Message):
    await db.get_user(message.from_user.id)
    bal = await get_fmt_bal(message.from_user.id)
    
    text = (
        f"👑 <b>ДОБРО ПОЖАЛОВАТЬ В CASINO ROYAL</b> 👑\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"💰 Баланс: <b>{bal} монет</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Испытай удачу и сорви джекпот!</i> 🎰"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb.main_menu())

# --- ГЛАВНОЕ МЕНЮ ---
@dp.callback_query(F.data == "menu_main")
async def menu_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    bal = await get_fmt_bal(cb.from_user.id)
    text = (
        f"🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 Твой баланс: <b>{bal} 💰</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Выбери раздел ниже:</i>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.main_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- МЕНЮ ИГР ---
@dp.callback_query(F.data == "menu_games")
async def menu_games(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        f"🎮 <b>ВЫБОР ИГРЫ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🎰 <b>Слоты</b> — до ×50\n"
        f"🎲 <b>Кости</b> — угадай число\n"
        f"🎡 <b>Рулетка</b> — классика\n"
        f"🃏 <b>Блэкджек</b> — против дилера\n"
        f"🪙 <b>Монетка</b> — 50 на 50\n"
        f"💣 <b>Мины</b> — скоро..."
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.games_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- ПРОФИЛЬ ---
@dp.callback_query(F.data == "menu_profile")
async def profile(cb: CallbackQuery):
    u = await db.get_user(cb.from_user.id)
    bal = await get_fmt_bal(u[0])
    
    total_games = u[2] + u[3]
    winrate = (u[2] / total_games * 100) if total_games > 0 else 0
    
    if u[1] > 50000: vip = "👑 ПЛАТИНА"
    elif u[1] > 20000: vip = "💎 ЗОЛОТО"
    elif u[1] > 5000: vip = "🥇 СЕРЕБРО"
    else: vip = "🥉 БРОНЗА"

    text = (
        f"👤 <b>ПРОФИЛЬ ИГРОКА</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🆔 ID: <code>{u[0]}</code>\n"
        f"💎 Статус: <b>{vip}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 Баланс: <b>{bal} 💰</b>\n"
        f"🏆 Побед: <b>{u[2]}</b> | 💀 Поражений: <b>{u[3]}</b>\n"
        f"📈 Винрейт: <b>{winrate:.1f}%</b>\n"
        f"🎯 Ставок сделано: <b>{u[6]}</b>\n"
        f"🔥 Рекордный выигрыш: <b>{u[4]} 💰</b>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- ТОП ---
@dp.callback_query(F.data == "menu_top")
async def top(cb: CallbackQuery):
    rows = await db.get_leaderboard()
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text = "🏆 <b>ТОП-10 ИГРОКОВ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    
    for i, (uid, bal, wins) in enumerate(rows):
        text += f"{medals[i]} <code>{uid}</code> | <b>{bal:,} 💰</b> | {wins} 🏆\n".replace(",", " ")
    
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- БОНУС ---
@dp.callback_query(F.data == "menu_bonus")
async def bonus(cb: CallbackQuery):
    ok, res = await db.claim_bonus(cb.from_user.id)
    if not ok:
        h, m = res // 3600, (res % 3600) // 60
        await cb.answer(f"⏰ Бонус будет доступен через {h}ч {m}м", show_alert=True)
        return
    
    await cb.answer(f"🎁 Ты получил {res} 💰!", show_alert=True)
    bal = await get_fmt_bal(cb.from_user.id)
    
    text = (
        f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Ты получил <b>{res} 💰</b>!\n"
        f"💰 Новый баланс: <b>{bal} 💰</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Возвращайся через 24 часа!</i>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    except TelegramBadRequest:
        pass

# --- VIP ---
@dp.callback_query(F.data == "menu_vip")
async def vip_menu(cb: CallbackQuery):
    text = (
        f"💎 <b>VIP-СИСТЕМА</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Статус зависит от твоего баланса:\n\n"
        f"🥉 <b>Бронза</b> — до 5 000 💰\n"
        f"🥇 <b>Серебро</b> — от 5 000 💰\n"
        f"💎 <b>Золото</b> — от 20 000 💰\n"
        f"👑 <b>Платина</b> — от 50 000 💰\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Скоро VIP будет давать бонусы к выигрышу!</i>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- МАГАЗИН ---
@dp.callback_query(F.data == "menu_shop")
async def shop_menu(cb: CallbackQuery):
    text = (
        f"🛒 <b>МАГАЗИН</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Товары скоро появятся!\n\n"
        f"Здесь можно будет купить:\n"
        f"• 🍀 Буст удачи\n"
        f"• 🛡 Страховку от проигрыша\n"
        f"• 🎨 Кастомные темы\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Следи за обновлениями!</i>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- КВЕСТЫ ---
@dp.callback_query(F.data == "menu_quests")
async def quests_menu(cb: CallbackQuery):
    text = (
        f"📜 <b>ЕЖЕДНЕВНЫЕ КВЕСТЫ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Задания появятся совсем скоро!\n\n"
        f"Примеры будущих квестов:\n"
        f"• Сделай 10 ставок ➡ +200 💰\n"
        f"• Выиграй 5 раз подряд ➡ +500 💰\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Готовим для тебя интересные задания!</i>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    except TelegramBadRequest:
        pass
    await cb.answer()

# --- СТАВКИ ---
@dp.callback_query(F.data.in_({"game_slots", "game_dice", "game_coin", "game_roulette"}))
async def choose_bet(cb: CallbackQuery):
    game = cb.data.replace("game_", "")
    names = {"slots":"🎰 СЛОТЫ", "dice":"🎲 КОСТИ", "coin":"🪙 МОНЕТКА", "roulette":"🎡 РУЛЕТКА"}
    bal = await get_fmt_bal(cb.from_user.id)
    
    text = (
        f"{names[game]}\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 Баланс: <b>{bal} 💰</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Выбери размер ставки:</i>"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.bet_menu(game))
    except TelegramBadRequest:
        pass
    await cb.answer()

@dp.callback_query(F.data.startswith("bet_"))
async def process_bet(cb: CallbackQuery):
    _, game, amount = cb.data.split("_")
    balance = await db.get_balance(cb.from_user.id)
    bet = balance if amount == "all" else int(amount)
    
    if bet <= 0 or bet > balance:
        return await cb.answer("❌ Недостаточно средств!", show_alert=True)

    if game == "slots":
        await play_slots(cb, bet)
    elif game == "dice":
        await cb.message.edit_text(f"🎲 Ставка: <b>{bet} 💰</b>\n➖➖➖➖➖➖➖➖\nНа что ставишь?", parse_mode="HTML", reply_markup=kb.dice_choice(bet))
    elif game == "coin":
        await cb.message.edit_text(f"🪙 Ставка: <b>{bet} 💰</b>\n➖➖➖➖➖➖➖➖\nОрёл или решка?", parse_mode="HTML", reply_markup=kb.coin_choice(bet))
    elif game == "roulette":
        await cb.message.edit_text(f"🎡 Ставка: <b>{bet} 💰</b>\n➖➖➖➖➖➖➖➖\nВыбери сектор:", parse_mode="HTML", reply_markup=kb.roulette_choice(bet))
    await cb.answer()

# (Остальные игры: Слоты, Кости, Монетка, Рулетка, Блэкджек...)
# Вставь сюда код игр из предыдущего сообщения, он не менялся.
# ...
