import os, random, time, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
import games as g
import keyboards as kb

# Безопасный запуск токена (сработает, даже если не настроить Render)
BOT_TOKEN = os.getenv("BOT_TOKEN", "9179387154:AAESWQmwzVMhO0J4lkvDXDdxKnH1JmZElYc")
ADMIN_ID = 123456789  # ЗАМЕНИ НА СВОЙ ID!

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Blackjack(StatesGroup):
    playing = State()

class RouletteState(StatesGroup):
    waiting_number = State()

# --- ХЕЛПЕРЫ ---
async def format_balance(uid):
    bal = await db.get_balance(uid)
    return f"{bal:,}".replace(",", " ")

# --- СТАРТ ---
@dp.message(CommandStart())
async def start(message: Message):
    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try: ref_id = int(args[1].replace("ref_", ""))
        except: pass
    
    user = await db.get_user(message.from_user.id)
    if ref_id and ref_id != message.from_user.id and not user[8]:
        await db.add_referral(ref_id, message.from_user.id)
    
    bal = await format_balance(message.from_user.id)
    await message.answer(
        f"🎰 <b>Добро пожаловать в Casino Simulator!</b>\n\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"💰 Твой баланс: <b>{bal} монет</b>\n\n"
        f"<i>Испытай удачу и попади в топ!</i>",
        parse_mode="HTML", reply_markup=kb.main_menu()
    )

# --- МЕНЮ ---
@dp.callback_query(F.data == "menu_main")
async def menu_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    bal = await format_balance(cb.from_user.id)
    await cb.message.edit_text(
        f"🏠 <b>Главное меню</b>\n\n💰 Баланс: <b>{bal} 💰</b>",
        parse_mode="HTML", reply_markup=kb.main_menu()
    )
    await cb.answer()

@dp.callback_query(F.data == "menu_games")
async def menu_games(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        "🎮 <b>Выбери игру</b>\n\nИспытай удачу в одной из наших игр!",
        parse_mode="HTML", reply_markup=kb.games_menu()
    )
    await cb.answer()

@dp.callback_query(F.data == "menu_profile")
async def profile(cb: CallbackQuery):
    u = await db.get_user(cb.from_user.id)
    vip_names = ["🥉 Новичок", "🥈 Бронза", "🥇 Серебро", "💎 Золото", "👑 Платина"]
    vip = vip_names[min(u[6], 4)]
    
    text = (
        f"👤 <b>Профиль игрока</b>\n───────────────\n"
        f"🆔 ID: <code>{u[0]}</code>\n"
        f"💎 Статус: <b>{vip}</b>\n───────────────\n"
        f"💰 Баланс: <b>{await format_balance(u[0])} 💰</b>\n"
        f"🏆 Побед: <b>{u[2]}</b> | 💀 Поражений: <b>{u[3]}</b>\n"
        f"🎯 Всего ставок: <b>{u[7]}</b>\n"
        f"🔥 Рекорд: <b>{u[4]} 💰</b>\n"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    await cb.answer()

@dp.callback_query(F.data == "menu_top")
async def top(cb: CallbackQuery):
    rows = await db.get_leaderboard()
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text = "🏆 <b>Топ-10 игроков</b>\n───────────────\n"
    if not rows:
        text += "Пока пусто 😴"
    for i, (uid, bal) in enumerate(rows):
        text += f"{medals[i]} <code>{uid}</code> — <b>{bal:,} 💰</b>\n".replace(",", " ")
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_main())
    await cb.answer()

@dp.callback_query(F.data == "menu_bonus")
async def bonus(cb: CallbackQuery):
    ok, res = await db.claim_bonus(cb.from_user.id)
    if not ok:
        h, m = res // 3600, (res % 3600) // 60
        await cb.answer(f"⏰ Бонус будет доступен через {h}ч {m}м", show_alert=True)
        return
    await cb.answer(f"🎁 Ты получил {res} 💰!", show_alert=True)
    await cb.message.edit_text(
        f"🎁 <b>Ежедневный бонус!</b>\n\nТы получил <b>500 💰</b>\n💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>",
        parse_mode="HTML", reply_markup=kb.back_main()
    )

# --- СТАВКИ ---
@dp.callback_query(F.data.in_({"game_slots", "game_dice", "game_coin", "game_roulette"}))
async def choose_bet(cb: CallbackQuery):
    game = cb.data.replace("game_", "")
    names = {"slots":"🎰 Слоты","dice":"🎲 Кости","coin":"🪙 Монетка","roulette":"🎡 Рулетка"}
    await cb.message.edit_text(
        f"{names[game]}\n\n💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>\n\nВыбери размер ставки:",
        parse_mode="HTML", reply_markup=kb.bet_menu(game)
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("bet_"))
async def process_bet(cb: CallbackQuery):
    _, game, amount = cb.data.split("_")
    balance = await db.get_balance(cb.from_user.id)
    bet = balance if amount == "all" else int(amount)
    
    if bet <= 0 or bet > balance:
        await cb.answer("❌ Недостаточно средств!", show_alert=True)
        return

    if game == "slots":
        await play_slots(cb, bet)
    elif game == "dice":
        await cb.message.edit_text(f"🎲 Ставка: <b>{bet} 💰</b>\n\nНа что ставишь?", parse_mode="HTML", reply_markup=kb.dice_choice(bet))
    elif game == "coin":
        await cb.message.edit_text(f"🪙 Ставка: <b>{bet} 💰</b>\n\nОрёл или решка?", parse_mode="HTML", reply_markup=kb.coin_choice(bet))
    elif game == "roulette":
        await cb.message.edit_text(f"🎡 Ставка: <b>{bet} 💰</b>\n\nВыбери сектор:", parse_mode="HTML", reply_markup=kb.roulette_choice(bet))
    await cb.answer()

# --- ИГРЫ ---
async def play_slots(cb, bet):
    await db.change_balance(cb.from_user.id, -bet)
    reels = g.spin_slots()
    mult = g.slots_multiplier(reels)
    prize = int(bet * mult)
    if prize: await db.change_balance(cb.from_user.id, prize)
    await db.record_game(cb.from_user.id, prize > 0, bet, prize)

    net = prize - bet
    res_text = f"<b>+{net}</b> 💰" if net >= 0 else f"<b>{net}</b> 💰"
    text = (
        f"🎰 <b>Слоты</b>\n───────────────\n"
        f"| {' | '.join(reels)} |\n───────────────\n"
        f"Ставка: <b>{bet} 💰</b>\nВыигрыш: {res_text}\n"
        f"💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.after_game("slots"))

@dp.callback_query(F.data.startswith("dice_"))
async def play_dice(cb: CallbackQuery):
    _, choice, bet = cb.data.split("_")
    bet = int(bet)
    if bet > await db.get_balance(cb.from_user.id):
        await cb.answer("❌ Недостаточно средств", show_alert=True); return

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
    res_text = f"<b>+{net}</b> 💰" if net >= 0 else f"<b>{net}</b> 💰"
    text = (
        f"🎲 <b>Кости</b>\n───────────────\n"
        f"Выпало: {g.DICE_EMOJI[roll-1]} <b>{roll}</b>\n───────────────\n"
        f"Ставка: <b>{bet} 💰</b>\nВыигрыш: {res_text}\n"
        f"💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.after_game("dice"))
    await cb.answer()

@dp.callback_query(F.data.startswith("coin_"))
async def play_coin(cb: CallbackQuery):
    _, choice, bet = cb.data.split("_")
    bet = int(bet)
    if bet > await db.get_balance(cb.from_user.id):
        await cb.answer("❌ Недостаточно средств", show_alert=True); return

    await db.change_balance(cb.from_user.id, -bet)
    result = g.flip_coin()
    won = result == choice
    prize = bet * 2 if won else 0
    if prize: await db.change_balance(cb.from_user.id, prize)
    await db.record_game(cb.from_user.id, won, bet, prize)

    emoji = "🪙" if result == "heads" else "🦅"
    name = "Орёл" if result == "heads" else "Решка"
    net = prize - bet
    res_text = f"<b>+{net}</b> 💰" if net >= 0 else f"<b>{net}</b> 💰"
    text = (
        f"🪙 <b>Монетка</b>\n───────────────\n"
        f"Выпало: {emoji} <b>{name}</b>\n───────────────\n"
        f"Ставка: <b>{bet} 💰</b>\nВыигрыш: {res_text}\n"
        f"💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.after_game("coin"))
    await cb.answer()

@dp.callback_query(F.data.startswith("roul_"))
async def play_roulette(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")
    if parts[1] == "num":
        bet = int(parts[2])
        await state.update_data(bet=bet)
        await state.set_state(RouletteState.waiting_number)
        await cb.message.edit_text(f"🎯 Ставка <b>{bet} 💰</b> на число\n\nОтправь число от 0 до 36:", parse_mode="HTML", reply_markup=kb.back_main())
        await cb.answer(); return

    choice, bet = parts[1], int(parts[2])
    if bet > await db.get_balance(cb.from_user.id):
        await cb.answer("❌ Недостаточно средств", show_alert=True); return

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
    res_text = f"<b>+{net}</b> 💰" if net >= 0 else f"<b>{net}</b> 💰"
    text = (
        f"🎡 <b>Рулетка</b>\n───────────────\n"
        f"Выпало: {color_emoji} <b>{num}</b>\n───────────────\n"
        f"Ставка: <b>{bet} 💰</b>\nВыигрыш: {res_text}\n"
        f"💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.after_game("roulette"))
    await cb.answer()

@dp.message(RouletteState.waiting_number)
async def roulette_number(message: Message, state: FSMContext):
    try:
        num = int(message.text)
        if not 0 <= num <= 36: raise ValueError
    except:
        await message.answer("❌ Введи число от 0 до 36"); return
    
    data = await state.get_data()
    bet = data["bet"]
    await state.clear()

    if bet > await db.get_balance(message.from_user.id):
        await message.answer("❌ Недостаточно средств", reply_markup=kb.main_menu()); return

    await db.change_balance(message.from_user.id, -bet)
    result = g.spin_roulette()
    won = result == num
    prize = bet * 36 if won else 0
    if prize: await db.change_balance(message.from_user.id, prize)
    await db.record_game(message.from_user.id, won, bet, prize)

    color = g.roulette_color(result)
    emoji = {"red":"🔴","black":"⚫","green":"🟢"}[color]
    net = prize - bet
    res_text = f"<b>+{net}</b> 💰" if net >= 0 else f"<b>{net}</b> 💰"
    text = (
        f"🎯 <b>Рулетка (Число)</b>\n───────────────\n"
        f"Выпало: {emoji} <b>{result}</b> (твоё: {num})\n───────────────\n"
        f"Ставка: <b>{bet} 💰</b>\nВыигрыш: {res_text}\n"
        f"💰 Баланс: <b>{await format_balance(message.from_user.id)} 💰</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb.after_game("roulette"))

# --- БЛЭКДЖЕК ---
@dp.callback_query(F.data == "game_blackjack")
async def bj_start(cb: CallbackQuery, state: FSMContext):
    bal = await db.get_balance(cb.from_user.id)
    bet = 50
    if bal < bet:
        await cb.answer("❌ Нужно минимум 50 💰", show_alert=True); return
    
    await db.change_balance(cb.from_user.id, -bet)
    deck = g.new_deck(); random.shuffle(deck)
    player, dealer = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    await state.update_data(deck=deck, player=player, dealer=dealer, bet=bet)
    await state.set_state(Blackjack.playing)
    await show_bj(cb, state, "Игра началась!")

async def show_bj(cb, state, note=""):
    data = await state.get_data()
    p, d = data["player"], data["dealer"]
    text = (
        f"🃏 <b>Блэкджек</b>\n───────────────\n"
        f"Твои карты: {g.fmt_hand(p)} = <b>{g.hand_value(p)}</b>\n"
        f"Дилер: {g.fmt_hand([d[0]])} + 🂠\n───────────────\n"
        f"{note}\n💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.bj_buttons())
    await cb.answer()

@dp.callback_query(F.data == "bj_hit")
async def bj_hit(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("deck"): return await cb.answer("Колода пуста")
    data["player"].append(data["deck"].pop())
    await state.update_data(**data)
    if g.hand_value(data["player"]) > 21:
        await bj_finish(cb, state, "💀 Перебор! Ты проиграл.")
    else:
        await show_bj(cb, state, "Ещё карту или хватит?")

@dp.callback_query(F.data == "bj_stand")
async def bj_stand(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    p_val = g.hand_value(data["player"])
    while g.hand_value(data["dealer"]) < 17:
        data["dealer"].append(data["deck"].pop())
    d_val = g.hand_value(data["dealer"])
    
    if d_val > 21 or p_val > d_val:
        await bj_finish(cb, state, "🎉 Ты выиграл!", win=True)
    elif p_val == d_val:
        await bj_finish(cb, state, "🤝 Ничья.", draw=True)
    else:
        await bj_finish(cb, state, "😢 Дилер выиграл.")

async def bj_finish(cb, state, note, win=False, draw=False):
    data = await state.get_data()
    bet = data["bet"]
    
    if win:
        await db.change_balance(cb.from_user.id, bet * 2)
        await db.record_game(cb.from_user.id, True, bet, bet * 2)
    elif draw:
        await db.change_balance(cb.from_user.id, bet)
    else:
        await db.record_game(cb.from_user.id, False, bet, 0)
        
    await state.clear()
    text = (
        f"🃏 <b>Итог Блэкджека</b>\n───────────────\n"
        f"Твои: {g.fmt_hand(data['player'])} = <b>{g.hand_value(data['player'])}</b>\n"
        f"Дилер: {g.fmt_hand(data['dealer'])} = <b>{g.hand_value(data['dealer'])}</b>\n───────────────\n"
        f"{note}\n💰 Баланс: <b>{await format_balance(cb.from_user.id)} 💰</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb.after_game("blackjack"))
    await cb.answer()

# --- АДМИНКА ---
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("👑 <b>Админ-панель</b>\n\n/give ID сумма\n/stats", parse_mode="HTML")

@dp.message(Command("give"))
async def admin_give(message: Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = message.text.split()
        await db.change_balance(int(uid), int(amount))
        await message.answer(f"✅ Выдано {amount} 💰 пользователю {uid}")
    except:
        await message.answer("❌ Формат: /give ID сумма")

@dp.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id != ADMIN_ID: return
    import aiosqlite
    async with aiosqlite.connect(db.DB) as d:
        async with d.execute("SELECT COUNT(*), SUM(balance) FROM users") as cur:
            users, total_bal = await cur.fetchone()
    await message.answer(f"📊 Юзеров: {users}\n💰 Монет в системе: {total_bal or 0}")

# --- ЗАПУСК ДЛЯ ЛОКАЛЬНОГО ТЕСТА (не для Render) ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
