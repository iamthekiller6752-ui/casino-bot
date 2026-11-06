from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🎮 ИГРАТЬ 🎮", callback_data="menu_games")],
        [B(text="👤 Профиль", callback_data="menu_profile"), B(text="🏆 Топ-10", callback_data="menu_top")],
        [B(text="🎁 Бонус", callback_data="menu_bonus"), B(text="💎 VIP", callback_data="menu_vip")],
        [B(text="🛒 Магазин", callback_data="menu_shop"), B(text="📜 Квесты", callback_data="menu_quests")],
    ])

def games_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🎰 Слоты", callback_data="game_slots"), B(text="🎲 Кости", callback_data="game_dice")],
        [B(text="🎡 Рулетка", callback_data="game_roulette"), B(text="🃏 Блэкджек", callback_data="game_blackjack")],
        [B(text="🪙 Монетка", callback_data="game_coin"), B(text="💣 Мины", callback_data="game_mines")],
        [B(text="🔙 В главное меню", callback_data="menu_main")],
    ])

def bet_menu(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="10 💰", callback_data=f"bet_{game}_10"), B(text="50 💰", callback_data=f"bet_{game}_50"), B(text="100 💰", callback_data=f"bet_{game}_100")],
        [B(text="500 💰", callback_data=f"bet_{game}_500"), B(text="💸 ВСЁ 💸", callback_data=f"bet_{game}_all")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

def dice_choice(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔽 Меньше 4 (×1.9)", callback_data=f"dice_under_{bet}"), B(text="🔼 Больше 3 (×1.9)", callback_data=f"dice_over_{bet}")],
        [B(text="🎯 Ровно 1 (×5)", callback_data=f"dice_one_{bet}"), B(text="🎯 Ровно 6 (×5)", callback_data=f"dice_six_{bet}")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

def coin_choice(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🪙 Орёл (×2)", callback_data=f"coin_heads_{bet}"), B(text="🦅 Решка (×2)", callback_data=f"coin_tails_{bet}")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

def roulette_choice(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔴 Красное (×2)", callback_data=f"roul_red_{bet}"), B(text="⚫ Чёрное (×2)", callback_data=f"roul_black_{bet}")],
        [B(text="🟢 Зеро (×14)", callback_data=f"roul_green_{bet}"), B(text="🎯 Число (×36)", callback_data=f"roul_num_{bet}")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

def bj_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Взять карту", callback_data="bj_hit"), B(text="✋ Хватит", callback_data="bj_stand")]
    ])

def back_main():
    return InlineKeyboardMarkup(inline_keyboard=[[B(text="🔙 В главное меню", callback_data="menu_main")]])

def after_game(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔁 Играть ещё", callback_data=f"game_{game}")],
        [B(text="🏠 В меню", callback_data="menu_main")],
    ])
