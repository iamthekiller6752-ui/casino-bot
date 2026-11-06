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
    admin_give = State()
    admin_unban = State()
    admin_broadcast = State()
    bj = State()
    roul = State()

async def fmt_bal(uid):
    return f"{await db.get_balance(uid):,}".replace(",", " ")

async def safe_edit(cb: CallbackQuery, text: str, reply_markup=None):
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            pass
    await cb.answer()

# --- СТАРТ ---
@dp.message(CommandStart())
async def start(message: Message):
    user = await db.get_user(message.from_user.id)
    if user[10] == 1:
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

# --- ИГРЫ ---
@dp.callback_query(F.data == "menu_games")
async def menu_games(cb: CallbackQuery):
    text = "🎮 <b>ВЫБОР ИГРЫ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n<i>Нажми на игру для начала:</i>"
    await safe_edit(cb, text, kb.games_menu())

# (Сюда вставь обработчики игр: game_slots, bet_slots, dice, coin, roulette, blackjack)
# Они работают через safe_edit, поэтому будут плавно меняться.

# --- ЗАРАБОТОК ---
@dp.callback_query(F.data == "menu_work")
async def work_menu(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    now = int(time.time())
    last_work = user[9]
    
    if now - last_work < 3600:
        m = (3600 - (now - last_work)) // 60
        return await cb.answer(f"⏰ Ты устал. Отдохни еще {m} минут.", show_alert=True)
    
    reward = random.randint(100, 500)
    await db.change_balance(cb.from_user.id, reward)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET last_work = ? WHERE user_id = ?", (now, cb.from_user.id))
        await d.commit()
        
    text = (
        f"💼 <b>РАБОТА</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Ты успешно поработал!\n"
        f"Заработано: <b>+{reward} 💰</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖"
    )
    await safe_edit(cb, text, kb.back_menu())

# --- МАГАЗИН ---
@dp.callback_query(F.data == "menu_shop")
async def shop(cb: CallbackQuery):
    text = (
        f"🛒 <b>МАГАЗИН</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🏠 <b>Дом</b> (10 000 💰) — пассивный доход.\n"
        f"💎 <b>VIP</b> (50 000 💰) — бонусы и статус.\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖"
    )
    await safe_edit(cb, text, kb.shop_menu())

@dp.callback_query(F.data == "shop_buy_house")
async def buy_house(cb: CallbackQuery):
    bal = await db.get_balance(cb.from_user.id)
    if bal < 10000: return await cb.answer("❌ Мало денег!", show_alert=True)
    await db.change_balance(cb.from_user.id, -10000)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET house_id = 1 WHERE user_id = ?", (cb.from_user.id,))
        await d.commit()
    await cb.answer("✅ Дом куплен!", show_alert=True)
    await shop(cb)

@dp.callback_query(F.data == "shop_buy_vip")
async def buy_vip(cb: CallbackQuery):
    bal = await db.get_balance(cb.from_user.id)
    if bal < 50000: return await cb.answer("❌ Мало денег!", show_alert=True)
    await db.change_balance(cb.from_user.id, -50000)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET vip_level = 1 WHERE user_id = ?", (cb.from_user.id,))
        await d.commit()
    await cb.answer("👑 VIP куплен!", show_alert=True)
    await shop(cb)

# --- VIP ---
@dp.callback_query(F.data == "menu_vip")
async def vip_info(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    status = "👑 VIP Активен" if user[7] == 1 else "❌ Нет VIP"
    house = "🏠 Есть дом" if user[8] == 1 else "❌ Нет дома"
    text = f"💎 <b>ТВОЙ СТАТУС</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n{status}\n{house}"
    await safe_edit(cb, text, kb.back_menu())

# --- ОБМЕННИК ---
@dp.callback_query(F.data == "menu_exchange")
async def exchange_start(cb: CallbackQuery, state: FSMContext):
    text = (
        f"🔄 <b>ОБМЕННИК</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Напиши в чат ID игрока и сумму через пробел:\n"
        f"Пример: <code>123456789 500</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Для отмены нажми кнопку ниже.</i>"
    )
    await safe_edit(cb, text, kb.back_menu())
    await state.set_state(States.exchange)

@dp.message(States.exchange)
async def exchange_process(message: Message, state: FSMContext):
    if message.text == "Отмена" or message.text.startswith("/"):
        await state.clear()
        return await message.answer("Действие отменено.")
    try:
        target_id, amount = map(int, message.text.split())
        if amount <= 0: raise ValueError
    except:
        return await message.answer("❌ Неверный формат. Введи: ID Сумма (или нажми /start для выхода)")
    
    if target_id == message.from_user.id:
        return await message.answer("❌ Нельзя перевести себе.")
    
    bal = await db.get_balance(message.from_user.id)
    if bal < amount:
        return await message.answer("❌ Недостаточно средств.")
    
    await db.change_balance(message.from_user.id, -amount)
    await db.change_balance(target_id, amount)
    
    await message.answer(f"✅ Успешно переведено <b>{amount} 💰</b> игроку <code>{target_id}</code>", parse_mode="HTML")
    await state.clear()
    # Возвращаем меню
    await message.answer("🏠 Главное меню", reply_markup=kb.main_menu())

# --- ПРОФИЛЬ ---
@dp.callback_query(F.data == "menu_profile")
async def profile(cb: CallbackQuery):
    u = await db.get_user(cb.from_user.id)
    bal = await fmt_bal(u[0])
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🆔 ID: <code>{u[0]}</code>\n"
        f"💰 Баланс: <b>{bal} 💰</b>\n"
        f"🏆 Побед: <b>{u[2]}</b> | 💀 Поражений: <b>{u[3]}</b>\n"
        f"🏠 Дом: <b>{'Да' if u[8] == 1 else 'Нет'}</b>\n"
        f"👑 VIP: <b>{'Да' if u[7] == 1 else 'Нет'}</b>"
    )
    await safe_edit(cb, text, kb.back_menu())

# --- ТОП ---
@dp.callback_query(F.data == "menu_top")
async def top(cb: CallbackQuery):
    rows = await db.get_leaderboard()
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text = "🏆 <b>ТОП-10</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    for i, (uid, bal, wins) in enumerate(rows):
        text += f"{medals[i]} <code>{uid}</code> | <b>{bal:,} 💰</b>\n".replace(",", " ")
    await safe_edit(cb, text, kb.back_menu())

# --- ОБНОВЛЕНИЯ ---
@dp.callback_query(F.data == "menu_updates")
async def updates(cb: CallbackQuery):
    online = await db.get_online_count()
    text = (
        f"📜 <b>ОБНОВЛЕНИЕ v2.0</b>\n"
        f"📅 Дата: 06.11.2026\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🟢 <b>Добавлено:</b>\n"
        f"• Меню на кнопках\n"
        f"• Работа (💼)\n"
        f"• Магазин (🛒)\n"
        f"• Обменник (🔄)\n"
        f"• Секретная админка\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👥 <b>Онлайн:</b> {online} чел."
    )
    await safe_edit(cb, text, kb.back_menu())

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

@dp.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery):
    await safe_edit(cb, "👑 <b>АДМИН-ПАНЕЛЬ</b>", kb.admin_menu())

@dp.callback_query(F.data.startswith("admin_"))
async def admin_actions(cb: CallbackQuery, state: FSMContext):
    action = cb.data.split("_")[1]
    if action == "ban":
        await safe_edit(cb, "Введите ID игрока для бана:", kb.back_to_admin())
        await state.set_state(States.admin_ban)
    elif action == "unban":
        await safe_edit(cb, "Введите ID игрока для разбана:", kb.back_to_admin())
        await state.set_state(States.admin_unban)
    elif action == "give":
        await safe_edit(cb, "Введите `ID Сумма` для выдачи:", kb.back_to_admin())
        await state.set_state(States.admin_give)
    elif action == "broadcast":
        await safe_edit(cb, "Введите текст для рассылки:", kb.back_to_admin())
        await state.set_state(States.admin_broadcast)

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

# (Рассылка опущена для краткости, работает по такому же принципу через state)
