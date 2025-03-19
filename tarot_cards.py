tarot_deck = [
    {"name": "Шут", "meaning": "Начало, невинность, спонтанность"},
    {"name": "Маг", "meaning": "Сила воли, творчество, мастерство"},
    # Добавьте остальные карты...
]

def draw_cards(num_cards):
    import random
    return random.sample(tarot_deck, num_cards)