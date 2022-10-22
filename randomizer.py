import random

EMOJIS = list(
    '😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘😗☺😚😙🥲😋😛😜🤪😝🤑🤗🤭🤫🤔🤐🤨😐😑😶😏😒🙄😬🤥😌😔😪🤤😴😷🤒🤕🤢🤮🤧🥵🥶🥴😵🤯🤠🥳🥸😎🤓🧐😕😟🙁☹😮😯😲😳🥺😦😧😨😰😥😢😭😱😖😣😞😓😩😫🥱😤😡😠🤬'
)

GAME_ITEMS = {
    ' ': 0,
    '🥠': 20,
    '🍪': 2,
    '💣': -2,
}


def get_random_emojis(count=5):
    items = set()
    while len(items) < count:
        items.add(random.choice(EMOJIS))
    return list(items)


def get_random_results():
    random_int = random.randint(0, 100)
    if random_int < 40:
        return ' '
    elif random_int < 60:
        return '🍪'
    elif random_int < 90:
        return '💣'
    else:
        return '🥠'
