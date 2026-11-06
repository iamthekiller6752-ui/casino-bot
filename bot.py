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
ADMIN_PASSWORD = "04172014" # Пароль для админки
MAIN_ADMIN_ID = 123456789 # Твой ID для рассылки (замени)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- СОСТОЯНИЯ ---
class GameStates(StatesGroup):
    blackjack = State()
    roulette = State()

class ActionStates(StatesGroup):
    exchange_waiting = State()
    admin_auth = State()
    admin_ban = State()
    admin_give = State()

# --- ХЕЛПЕРЫ ---
async def fmt_bal(uid):
    return f"{await db.get_balance(uid):,}".replace(",", " ")

# --- СТАРТ ---
@dp.message(CommandStart())
async def start(message: Message):
    user = await db.get_user(message.from_user.id)
    if user[10] == 1: # Проверка на бан
        return await message.answer("❌ Вы забанены в этом боте.")
    
    bal = await fmt_bal(message.from_user.id)
    await message.answer(
        f"👑 <b>ДОБРО ПОЖАЛОВАТЬ В CASINO ROYAL</b> 👑\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"💰 Баланс: <b>{bal} монет</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Используй меню снизу для навигации!</i>",
        parse_mode="HTML", reply_markup=kb.main_reply_menu()
    )

@dp.callback_query(F.data == "menu_main")
async def go_main(cb: CallbackQuery):
    await cb.message.delete()
    await cb.message.answer("🏠 Возврат в главное меню", reply_markup=kb.main_reply_menu())
    await cb.answer()

# --- РАЗДЕЛ: ИГРЫ ---
@dp.message(F.text == "🎰 Играть")
async def games_menu(message: Message):
    await message.answer("🎮 <b>Выбери игру:</b>", reply_markup=kb.games_inline(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_games")
async def back_to_games(cb: CallbackQuery):
    await cb.message.edit_text("🎮 <b>Выбери игру:</b>", reply_markup=kb.games_inline(), parse_mode="HTML")

@dp.callback_query(F.data.in_({"game_slots", "game_dice", "game_coin", "game_roulette"}))
async def choose_bet(cb: CallbackQuery):
    game = cb.data.replace("game_", "")
    bal = await fmt_bal(cb.from_user.id)
    await cb.message.edit_text(f"💰 Баланс: <b>{bal} 💰</b>\n\nВыбери ставку:", parse_mode="HTML", reply_markup=kb.bet_menu(game))
    await cb.answer()

# ВСТАВЬ СЮДА ЛОГИКУ ИГР (Слоты, Кости, Рулетка, Блэкджек) ИЗ ПРЕДЫДУЩЕГО КОДА
# ... (чтобы не раздувать ответ, я пропустил их, они не изменились) ...

# --- РАЗДЕЛ: ЗАРАБОТОК ---
@dp.message(F.text == "💼 Заработок")
async def work_menu(message: Message):
    user = await db.get_user(message.from_user.id)
    now = int(time.time())
    last_work = user[9]
    
    if now - last_work < 3600: # Кулдаун 1 час
        m = (3600 - (now - last_work)) // 60
        return await message.answer(f"⏰ Ты устал. Отдохни еще {m} минут перед следующей работой.")
    
    reward = random.randint(100, 500)
    await db.change_balance(message.from_user.id, reward)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET last_work = ? WHERE user_id = ?", (now, message.from_user.id))
        await d.commit()
        
    await message.answer(
        f"💼 <b>Работа выполнена!</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"Ты заработал: <b>+{reward} 💰</b>\n"
        f"Возвращайся через час!", 
        parse_mode="HTML"
    )

# --- РАЗДЕЛ: МАГАЗИН ---
@dp.message(F.text == "🛒 Магазин")
async def shop_menu(message: Message):
    await message.answer(
        "🛒 <b>Магазин недвижимости и статусов</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "🏠 <b>Дом</b> (10 000 💰) — дает пассивный доход раз в сутки.\n"
        "💎 <b>VIP</b> (50 000 💰) — увеличивает ежедневный бонус в 2 раза.\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖",
        parse_mode="HTML", reply_markup=kb.shop_menu()
    )

@dp.callback_query(F.data == "shop_buy_house")
async def buy_house(cb: CallbackQuery):
    bal = await db.get_balance(cb.from_user.id)
    if bal < 10000:
        return await cb.answer("❌ Недостаточно средств!", show_alert=True)
    await db.change_balance(cb.from_user.id, -10000)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET house_id = 1 WHERE user_id = ?", (cb.from_user.id,))
        await d.commit()
    await cb.answer("✅ Ты купил дом! Теперь получаешь пассивный доход.", show_alert=True)

@dp.callback_query(F.data == "shop_buy_vip")
async def buy_vip(cb: CallbackQuery):
    bal = await db.get_balance(cb.from_user.id)
    if bal < 50000:
        return await cb.answer("❌ Недостаточно средств!", show_alert=True)
    await db.change_balance(cb.from_user.id, -50000)
    async with db.aiosqlite.connect(db.DB) as d:
        await d.execute("UPDATE users SET vip_level = 1 WHERE user_id = ?", (cb.from_user.id,))
        await d.commit()
    await cb.answer("👑 Ты купил VIP! Бонусы увеличены.", show_alert=True)

# --- РАЗДЕЛ: VIP-СТАТУС ---
@dp.message(F.text == "💎 VIP-Статус")
async def vip_info(message: Message):
    user = await db.get_user(message.from_user.id)
    status = "👑 VIP Активен" if user[7] == 1 else "❌ Нет VIP"
    house = "🏠 Есть дом" if user[8] == 1 else "❌ Нет дома"
    await message.answer(f"💎 Твой статус:\n{status}\n{house}")

# --- РАЗДЕЛ: ОБМЕННИК ---
@dp.message(F.text == "🔄 Обменник")
async def exchange_menu(message: Message, state: FSMContext):
    await message.answer("💸 Введи ID игрока и сумму через пробел (например: `123456789 500`), чтобы перевести деньги:", parse_mode="Markdown")
    await state.set_state(ActionStates.exchange_waiting)

@dp.message(ActionStates.exchange_waiting)
async def process_exchange(message: Message, state: FSMContext):
    try:
        target_id, amount = map(int, message.text.split())
        if amount <= 0: raise ValueError
    except:
        return await message.answer("❌ Неверный формат. Введи: `ID Сумма`")
    
    if target_id == message.from_user.id:
        return await message.answer("❌ Нельзя перевести самому себе.")
    
    bal = await db.get_balance(message.from_user.id)
    if bal < amount:
        return await message.answer("❌ Недостаточно средств.")
    
    await db.change_balance(message.from_user.id, -amount)
    await db.change_balance(target_id, amount)
    
    await message.answer(f"✅ Успешно переведено <b>{amount} 💰</b> игроку <code>{target_id}</code>", parse_mode="HTML")
    await state.clear()

# --- РАЗДЕЛ: ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    u = await db.get_user(message.from_user.id)
    bal = await fmt_bal(u[0])
    await message.answer(
        f"👤 <b>ПРОФИЛЬ</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🆔 ID: <code>{u[0]}</code>\n"
        f"💰 Баланс: <b>{bal} 💰</b>\n"
        f"🏆 Побед: <b>{u[2]}</b> | 💀 Поражений: <b>{u[3]}</b>\n"
        f"🏠 Дом: <b>{'Да' if u[8] == 1 else 'Нет'}</b>\n"
        f"👑 VIP: <b>{'Да' if u[7] == 1 else 'Нет'}</b>",
        parse_mode="HTML"
    )

# --- РАЗДЕЛ: ТОП-10 ---
@dp.message(F.text == "🏆 Топ-10")
async def top(message: Message):
    rows = await db.get_leaderboard()
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text = "🏆 <b>ТОП-10 ИГРОКОВ</b>\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    for i, (uid, bal, wins) in enumerate(rows):
        text += f"{medals[i]} <code>{uid}</code> | <b>{bal:,} 💰</b>\n".replace(",", " ")
    await message.answer(text, parse_mode="HTML")

# --- РАЗДЕЛ: ОБНОВЛЕНИЯ ---
@dp.message(F.text == "📜 Обновления")
async def changelog(message: Message):
    online = await db.get_online_count()
    text = (
        f"📜 <b>ИСТОРИЯ ОБНОВЛЕНИЙ (v2.0)</b>\n"
        f"📅 Дата: 06.11.2026\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🟢 <b>Добавлено:</b>\n"
        f"• Глобальное меню на кнопках\n"
        f"• Система работы (💼)\n"
        f"• Магазин домов и VIP (🛒)\n"
        f"• Перевод монет другим игрокам (🔄)\n"
        f"• Секретная админ-панель\n\n"
        f"🔴 <b>Убрано:</b>\n"
        f"• Баги с зависанием кнопок\n\n"
        f"👥 <b>Онлайн сейчас:</b> {online} чел."
    )
    await message.answer(text, parse_mode="HTML")

# --- СЕКРЕТНАЯ АДМИНКА ---
@dp.message(Command("adminpanelss"))
async def admin_start(message: Message, state: FSMContext):
    await message.answer("🔐 Введите пароль для доступа к Админ-Панели:")
    await state.set_state(ActionStates.admin_auth)

@dp.message(ActionStates.admin_auth)
async def admin_auth(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.clear()
        await message.answer("👑 <b>Добро пожаловать в Админ-Панель!</b>", parse_mode="HTML", reply_markup=kb.admin_menu())
    else:
        await message.answer("❌ Неверный пароль.")
        await state.clear()

@dp.callback_query(F.data.startswith("admin_"))
async def admin_actions(cb: CallbackQuery, state: FSMContext):
    action = cb.data.split("_")[1]
    if action == "ban":
        await cb.message.answer("Введите ID игрока для бана:")
        await state.set_state(ActionStates.admin_ban)
    elif action == "unban":
        await cb.message.answer("Введите ID игрока для разбана:")
        # Логика разбана (можно аналогично бану)
    elif action == "give":
        await cb.message.answer("Введите `ID Сумма` для выдачи:")
        await state.set_state(ActionStates.admin_give)
    elif action == "broadcast":
        await cb.message.answer("Введите текст для рассылки всем игрокам:")
        # Логика рассылки
    await cb.answer()

@dp.message(ActionStates.admin_ban)
async def process_ban(message: Message, state: FSMContext):
    try:
        target_id = int(message.text)
        async with db.aiosqlite.connect(db.DB) as d:
            await d.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (target_id,))
            await d.commit()
        await message.answer(f"✅ Игрок {target_id} забанен.")
    except:
        await message.answer("❌ Ошибка формата ID.")
    await state.clear()

@dp.message(ActionStates.admin_give)
async def process_give(message: Message, state: FSMContext):
    try:
        target_id, amount = map(int, message.text.split())
        await db.change_balance(target_id, amount)
        await message.answer(f"✅ Выдано {amount} 💰 игроку {target_id}.")
    except:
        await message.answer("❌ Ошибка. Формат: ID Сумма")
    await state.clear()
