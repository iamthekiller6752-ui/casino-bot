import random

# --- СЛОТЫ ---
SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🔔", "⭐", "💎"]
SLOT_PAYOUTS = {"🍒": 3, "🍋": 4, "🍊": 5, "🔔": 8, "⭐": 15, "💎": 50}

def spin_slots():
    return [random.choices(SLOT_SYMBOLS, weights=[30, 25, 20, 12, 8, 5])[0] for _ in range(3)]

def slots_multiplier(reels):
    a, b, c = reels
    if a == b == c: return SLOT_PAYOUTS[a]
    if a == b or b == c or a == c: return 1.2
    return 0

# --- КОСТИ ---
def roll_dice(): return random.randint(1, 6)
DICE_EMOJI = ["⚀","⚁","⚂","⚃","⚄","⚅"]

# --- РУЛЕТКА ---
def spin_roulette(): return random.randint(0, 36)
def roulette_color(n):
    if n == 0: return "green"
    red = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    return "red" if n in red else "black"

# --- БЛЭКДЖЕК ---
def new_deck():
    ranks = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    return [(r, s) for r in ranks for s in ["♠","♥","♦","♣"]]

def hand_value(hand):
    val, aces = 0, 0
    for r, _ in hand:
        if r in "JQK": val += 10
        elif r == "A": aces += 1; val += 11
        else: val += int(r)
    while val > 21 and aces:
        val -= 10; aces -= 1
    return val

def fmt_hand(hand):
    return " ".join(f"{r}{s}" for r, s in hand)

# --- МИНЫ ---
def generate_mines(field_size=9, mines_count=3):
    # Возвращает список индексов, где находятся мины (от 0 до 8)
    return set(random.sample(range(field_size), mines_count))
