from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B

# Главное меню (Сетка 2x4)
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🎰 Играть", callback_data="menu_games"), B(text="💼 Заработок", callback_data="menu_work")],
        [B(text="🛒 Магазин", callback_data="menu_shop"), B(text="💎 VIP", callback_data="menu_vip")],
        [B(text="🔄 Обменник", callback_data="menu_exchange"), B(text="👤 Профиль", callback_data="menu_profile")],
        [B(text="🏆 Топ-10", callback_data="menu_top"), B(text="📜 Обновления", callback_data="menu_updates")]
    ])

# Меню игр (Сетка 2x3)
def games_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🎰 Слоты", callback_data="game_slots"), B(text="🎲 Кости", callback_data="game_dice")],
        [B(text="🎡 Рулетка", callback_data="game_roulette"), B(text="🃏 Блэкджек", callback_data="game_blackjack")],
        [B(text="🪙 Монетка", callback_data="game_coin"), B(text="💣 Мины", callback_data="game_mines")],
        [B(text="🔙 Назад", callback_data="menu_main")]
    ])

# Меню ставок
def bet_menu(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="10 💰", callback_data=f"bet_{game}_10"), B(text="50 💰", callback_data=f"bet_{game}_50"), B(text="100 💰", callback_data=f"bet_{game}_100")],
        [B(text="500 💰", callback_data=f"bet_{game}_500"), B(text="💸 ВСЁ 💸", callback_data=f"bet_{game}_all")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

# Магазин
def shop_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🏠 Купить Дом (10 000 💰)", callback_data="shop_buy_house")],
        [B(text="💎 Купить VIP (50 000 💰)", callback_data="shop_buy_vip")],
        [B(text="🔙 Назад", callback_data="menu_main")]
    ])

# Админка
def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="👤 Забанить юзера", callback_data="admin_ban"), B(text="✅ Разбанить", callback_data="admin_unban")],
        [B(text="💰 Выдать деньги", callback_data="admin_give")],
        [B(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
        [B(text="🔙 Выйти в меню", callback_data="menu_main")]
    ])

# Универсальная кнопка "Назад"
def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[B(text="🔙 Назад", callback_data="menu_main")]])

def back_to_admin():
    return InlineKeyboardMarkup(inline_keyboard=[[B(text="🔙 В админ-меню", callback_data="admin_back")]])

# Кнопки после игры
def after_game(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔁 Играть ещё", callback_data=f"game_{game}")],
        [B(text="🔙 В меню", callback_data="menu_main")],
    ])

# Выбор в костях
def dice_choice(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔽 Меньше 4 (×1.9)", callback_data=f"dice_under_{bet}"), B(text="🔼 Больше 3 (×1.9)", callback_data=f"dice_over_{bet}")],
        [B(text="🎯 Ровно 1 (×5)", callback_data=f"dice_one_{bet}"), B(text="🎯 Ровно 6 (×5)", callback_data=f"dice_six_{bet}")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

# Выбор в монетке
def coin_choice(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🪙 Орёл (×2)", callback_data=f"coin_heads_{bet}"), B(text="🦅 Решка (×2)", callback_data=f"coin_tails_{bet}")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

# Выбор в рулетке
def roulette_choice(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔴 Красное (×2)", callback_data=f"roul_red_{bet}"), B(text="⚫ Чёрное (×2)", callback_data=f"roul_black_{bet}")],
        [B(text="🟢 Зеро (×14)", callback_data=f"roul_green_{bet}"), B(text="🎯 Число (×36)", callback_data=f"roul_num_{bet}")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

# Кнопки блэкджека
def bj_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Взять карту", callback_data="bj_hit"), B(text="✋ Хватит", callback_data="bj_stand")]
    ])
