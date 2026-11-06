from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton as KB

# Главное меню (Reply Keyboard - как на скриншоте)
def main_reply_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KB(text="🎰 Играть"), KB(text="💼 Заработок")],
        [KB(text="🛒 Магазин"), KB(text="💎 VIP-Статус")],
        [KB(text="🔄 Обменник"), KB(text="👤 Профиль")],
        [KB(text="🏆 Топ-10"), KB(text="📜 Обновления")]
    ], resize_keyboard=True)

def games_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🎰 Слоты", callback_data="game_slots"), B(text="🎲 Кости", callback_data="game_dice")],
        [B(text="🎡 Рулетка", callback_data="game_roulette"), B(text="🃏 Блэкджек", callback_data="game_blackjack")],
        [B(text="🪙 Монетка", callback_data="game_coin")],
        [B(text="🔙 Назад", callback_data="menu_main")]
    ])

def bet_menu(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="10 💰", callback_data=f"bet_{game}_10"), B(text="50 💰", callback_data=f"bet_{game}_50"), B(text="100 💰", callback_data=f"bet_{game}_100")],
        [B(text="500 💰", callback_data=f"bet_{game}_500"), B(text="💸 ВСЁ 💸", callback_data=f"bet_{game}_all")],
        [B(text="🔙 Назад", callback_data="menu_games")],
    ])

def shop_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🏠 Купить Дом (10 000 💰)", callback_data="shop_buy_house")],
        [B(text="💎 Купить VIP (50 000 💰)", callback_data="shop_buy_vip")],
        [B(text="🔙 Назад", callback_data="menu_main")]
    ])

def back_main_inline():
    return InlineKeyboardMarkup(inline_keyboard=[[B(text="🔙 В меню", callback_data="menu_main")]])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="👤 Забанить юзера", callback_data="admin_ban"), B(text="✅ Разбанить", callback_data="admin_unban")],
        [B(text="💰 Выдать деньги", callback_data="admin_give")],
        [B(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
    ])

def after_game(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔁 Играть ещё", callback_data=f"game_{game}")],
        [B(text="🔙 В меню", callback_data="menu_main")],
    ])
