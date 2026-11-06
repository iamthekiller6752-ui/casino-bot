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
MAIN_ADMIN_ID = 123456789 # Твой ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class States(StatesGroup):
    exchange = State()
    admin_auth = State()
    admin_ban = State()
    admin_unban = State()
    admin_give = State()

# Красивое форматирование имени
def get_display_name(username, first_name, user_id):
    if username:
        return f"@{username}"
    elif first_name:
        return first_name
    return f"ID:{user_id}"

async def fmt_bal(uid):
    return f"{await db.get_balance(uid):,}".replace(",", " ")

async def safe_edit(cb: CallbackQuery, text: str, reply_markup=None):
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            pass
    await cb.answer()

# --- СТАРТ (Передаем username и first_name) ---
@dp.message(CommandStart())
async def start(message: Message):
    user = await db.get_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if user[12] == 1: # Проверка на бан (индекс сдвинулся)
        return await message.answer("❌ Вы забанены в этом боте.")
    
    bal = await fmt_bal(message.from_user.id)
    await message.answer(
        f"👑 <b>CASINO ROYAL</b> 👑\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"💰 Баланс: <b>{bal} монет</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Выбирай действия на кнопках ниже:</i>",
        parse_mode="HTML", reply_markup=kb.main_menu()
    )

# --- ГЛАВНОЕ МЕНЮ ---
@dp.callback_query(F.data == "menu_main")
async def menu_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    bal = await fmt_bal(cb.from_user.id)
    text = (
        f"🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 Баланс: <b>{bal} 💰</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖"
    )
    await safe_edit(cb, text, kb.main_menu())

# --- ПРОФИЛЬ ---
@dp.callback_query(F.data == "menu_profile")
async def profile(cb: CallbackQuery):
    u = await db.get_user(cb.from_user.id)
    bal = await fmt_bal(u[0])
    
    # В базе u[1] - username, u[2] - first_name
    display_name = get_display_name(u[1], u[2], u[0])
    
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 Имя: <b>{display_name}</b>\n"
        f"💰 Баланс: <b>{bal} 💰</b>\n"
        f"🏆 Побед: <b>{u[4]}</b> | 💀 Поражений: <b>{u[5]}</b>\n"
        f"🏠 Дом: <b>{'Да' if u[10] == 1 else 'Нет'}</b>\n"
        f"👑 VIP: <b>{'Да' if u[9] == 1 else 'Нет'}</b>"
    )
    await safe_edit(cb, text, kb.back_menu())

# --- ТОП-10 ---
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

# --- ОБМЕННИК (Поиск по нику или ID) ---
@dp.callback_query(F.data == "menu_exchange")
async def exchange_start(cb: CallbackQuery, state: FSMContext):
    text = (
        f"🔄 <b>ОБМЕННИК</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Напиши в чат <b>@ник</b> (или ID) игрока и сумму:\n"
        f"Пример: <code>@durov 500</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Для отмены нажми кнопку ниже.</i>"
    )
    await safe_edit(cb, text, kb.back_menu())
    await state.set_state(States.exchange)

@dp.message(States.exchange)
async def exchange_process(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await state.clear()
        return await message.answer("Действие отменено. Используй /start.")
    
    try:
        target_str, amount_str = message.text.split()
        amount = int(amount_str)
        if amount <= 0: raise ValueError
    except:
        return await message.answer("❌ Неверный формат. Введи: @ник Сумма (или /start для выхода)")
    
    target_id = None
    if target_str.startswith("@"):
        # Ищем по юзернейму (без собачки)
        username = target_str[1:]
        target_id = await db.get_user_by_username(username)
        if not target_id:
            return await message.answer("❌ Игрок с таким @ником не найден в базе (он должен хотя бы раз зайти в бота).")
    else:
        # Пытаемся распознать как ID
        try:
            target_id = int(target_str)
        except:
            return await message.answer("❌ Неверный формат. Введи @ник или числовой ID.")
            
    if target_id == message.from_user.id:
        return await message.answer("❌ Нельзя перевести самому себе.")
    
    bal = await db.get_balance(message.from_user.id)
    if bal < amount:
        return await message.answer("❌ Недостаточно средств.")
    
    await db.change_balance(message.from_user.id, -amount)
    await db.change_balance(target_id, amount)
    
    await message.answer(f"✅ Успешно переведено <b>{amount} 💰</b> игроку <code>{target_str}</code>", parse_mode="HTML")
    await state.clear()
    
    # Возвращаем меню
    await message.answer("🏠 Главное меню", reply_markup=kb.main_menu())

# (Остальные функции: Игры, Работа, Магазин, VIP, Обновления, Админка — остаются такими же, 
# просто убедись, что при вызове db.get_user() передаются username и first_name)
