"""
Cat Voice - what the cat says, in a cat's voice.

Design rules (lovely pet, never a stressful one):
* Short lines (fit in one speech bubble), cat sounds first, words second.
* Needs are *asked for* sweetly ("snack?"), never guilt ("don't forget me").
* Personality changes the tone: social cats chatter, shy cats say less,
  playful cats bounce, calm cats purr.
* Memory makes it personal: it asks for its favourite toy, remembers you.
"""

import random

SOUNDS = ["mrrp", "mew", "prrr", "mrow", "nya"]

LINES = {
    # --- replies to what YOU do ------------------------------------------------
    "eat": ["nom nom nom 🐟", "mmm! tasty 😋", "*happy crunching*", "thank mew 💕", "best snack ever 🍗"],
    "purr": ["prrrrr~ 💕", "*headbutts your hand*", "more pets pls 🥰", "*slow blink* ❤️", "prrr... right there"],
    "play": ["pounce! 🐾", "again! again! ✨", "got it! 😸", "*wiggles butt*", "zoomies!! 💨"],
    "sleep": ["*curls up* 💤", "zzz... 🌙", "nap time~", "*tiny snore*"],
    "rest": ["*loaf mode* 🍞", "just chillin'", "*stretches* ahh~"],
    "groom": ["so fluffy now ✨", "*licks paw* thx!", "looking purrfect 💅"],
    "talk": ["mrrp? mrrp! 💬", "*chirps back*", "mew mew! (i agree)", "tell me more~"],
    "train": ["like this? 🎓", "*sits proudly*", "i'm learning! ⭐", "treat for a trick? 😼"],
    "hide": ["*peeks out* 👀", "...is it safe?", "*tiny box mode* 📦"],
    # --- needs, asked sweetly -------------------------------------------------
    "need_hungry": ["mrrp... snack? 🐟", "*looks at food bowl*", "tummy says mew 🍗", "is it dinner? 👀"],
    "need_sleepy": ["*big yawn* 😪", "sleepy... 💤", "nap soon? 🌙"],
    "need_lonely": ["*sits near you* 💕", "mrrp? play with me?", "*soft mew*", "pet me? 🥺"],
    "need_bored": ["got toys? 🧶", "*bats at nothing*", "let's play! 🎾"],
    # --- happy idle chatter (rare) --------------------------------------------
    "content": ["prrr~ ☀️", "*happy tail swish*", "i like it here 💕", "*slow blink* 😌", "life is good~"],
    "excited": ["wheee! ✨", "*zooms past* 💨", "so much energy! ⚡"],
    # --- moments ---------------------------------------------------------------
    "hover": ["oh hi! 👋", "*sniffs cursor*", "mrrp? ❤️", "hello hooman~", "*bonks your cursor*"],
    "hover_sleepy": ["*one eye opens*", "zzz... hi... 💤"],
    "achievement": ["✨ {name}! ✨", "we did it! {name} 🏆", "yay! {name} ⭐"],
    "minigame_win": ["caught it!! 🏆", "i'm a hunter! 😼", "*proud wiggle*"],
    "minigame_miss": ["so close! 😹", "next time!", "*pretends it meant that*"],
    # --- living on the desktop --------------------------------------------------
    "perch": ["nice view from up here ☀️", "*settles on the window* 😌", "king of the window 👑", "*dangles a paw*"],
    "perch_fall": ["whoa! 🙀", "hey, my window! 😹", "*lands on all fours* ✨"],
    "thrown": ["wiiiii! 🎢", "again!! ✨", "wheee~ 💨", "i can fly! 🪽"],
    "landed": ["*lands gracefully* ✨", "10/10 landing 😼", "*shakes fur*"],
    "bonk": ["boing! 😹"],
    "chase": ["got you! 🐾", "*pounces on cursor*", "it's fast! 😼"],
    "chase_tired": ["*pant pant* you win 😹", "it's too fast~ 💨", "*sits and stares at it*"],
    "gift_drop": ["i brought you something! 🎁", "for you~ 💕", "*drops a gift* look!"],
    "breakfast": ["breakfast time? ☀️🐟"],
    "bedtime": ["getting cozy... 🌙"],
}

TOY_EMOJI = {"ball": "🔴", "fish": "🐟", "mouse": "🐭", "bird": "🐦"}


def _sound(personality):
    social = personality.get("social", 0.5)
    snd = random.choice(SOUNDS)
    return f"{snd}{'~' if social > 0.5 else ''}"


def say(kind, cat=None, **fmt):
    """Return one line for a situation, or None if nothing fits."""
    options = LINES.get(kind)
    if not options:
        return None
    line = random.choice(options).format(**fmt) if fmt else random.choice(options)
    personality = getattr(cat, "personality", {}) if cat else {}
    # Chatty cats sometimes add a little sound in front
    if personality and kind not in ("achievement",) and random.random() < 0.25 + 0.3 * personality.get("social", 0.5):
        if not line.startswith(("*", "mrrp", "mew", "prrr", "mrow", "nya")):
            line = f"{_sound(personality)}! {line}"
    return line


def memory_line(cat):
    """A line that shows the cat remembers you (favourite toy / thing)."""
    graph = getattr(cat, "memory_graph", None)
    if graph is None:
        return None
    favs = [(name, val) for name, val in graph.favorites("stimulus", top=3) if name in TOY_EMOJI and val > 0.2]
    if favs and random.random() < 0.6:
        toy = favs[0][0]
        return random.choice([f"{toy} again? {TOY_EMOJI[toy]}", f"remember the {toy}? {TOY_EMOJI[toy]}",
                              f"i dreamt of the {toy} {TOY_EMOJI[toy]}"])
    if getattr(cat, "trust", 0) > 70:
        return random.choice(["you're my favorite hooman 💕", "*follows you everywhere*", "i missed you~ ❤️"])
    return None


ACTION_MEMORIES = {
    "play": "when we played together 🧶",
    "purr": "all those pets you gave me 💕",
    "eat": "that yummy snack 🐟",
    "groom": "when you brushed my fur ✨",
    "talk": "our little chats 💬",
    "train": "when i learned a trick 🎓",
    "perch": "watching the world from your windows ☀️",
    "chase_cursor": "chasing your cursor 🐾",
}


def gift_memory(cat):
    """The note inside a gift: a happy memory the cat kept from your time together."""
    graph = getattr(cat, "memory_graph", None)
    if graph is not None:
        favs = [(n, v) for n, v in graph.favorites("stimulus", top=4) if n in TOY_EMOJI and v > 0.1]
        if favs and random.random() < 0.5:
            toy = random.choice(favs)[0]
            return f"remember the {toy}? {TOY_EMOJI[toy]}"
        acts = [(n, v) for n, v in graph.favorites("action", top=5) if n in ACTION_MEMORIES and v > 0.05]
        if acts:
            return f"i remember {ACTION_MEMORIES[random.choice(acts)[0]]}"
    return random.choice(["this is for my favorite hooman 💕", "found it just for you~ ✨", "thank mew for taking care of me 🐾"])


def need_kind(cat):
    """Which gentle need line fits now (or None if all good)."""
    if cat.hunger > 75:
        return "need_hungry"
    if cat.energy < 20:
        return "need_sleepy"
    if cat.trust < 30 or cat.happiness < 25:
        return "need_lonely"
    if cat.happiness < 45 and cat.energy > 60:
        return "need_bored"
    return None


def idle_chatter(cat):
    """Rare spontaneous line when nothing is urgent."""
    if random.random() < 0.35:
        line = memory_line(cat)
        if line:
            return line
    if cat.energy > 80 and cat.happiness > 60:
        return say("excited", cat)
    if cat.happiness > 55:
        return say("content", cat)
    return None


def wellbeing(cat_status):
    """0-100 'health' score shown on hover: fed, rested and happy."""
    return round((100 - cat_status["hunger"]) * 0.35 + cat_status["energy"] * 0.3
                 + cat_status["happiness"] * 0.35)


def mood_word(cat_status):
    h = cat_status["happiness"]
    if cat_status["energy"] < 20:
        return "sleepy 😴"
    if cat_status["hunger"] > 75:
        return "peckish 🐟"
    if h > 75:
        return "so happy 😸"
    if h > 50:
        return "content 😺"
    if h > 25:
        return "a bit meh 😿"
    return "needs love 🥺"
