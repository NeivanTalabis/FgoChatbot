import random

RESPONSES = {
    "greeting": [
        "Ehehe, hello Master~ Ask me anything about FGO — servants, gacha, events, you name it!",
        "Hiya! I'm all ears for your FGO questions, big or small.",
        "Mm, good to see you! What's on your mind today — servants, story, gameplay?",
        "Fufu, welcome back~ What shall we talk about?",
    ],
    "game_info": [
        "FGO — Fate/Grand Order — is a turn-based RPG where you, a Master, command Servants: heroic spirits pulled from myth and history. The story follows Chaldea's fight to save humanity's future across different eras!",
        "It's a gacha RPG at heart, built on the Fate franchise. You'll recruit Servants, fight through story chapters called Singularities, and slowly uncover why history itself is falling apart.",
        "Think turn-based battles plus a long, heavy story — FGO leans more story-and-character focused than most mobile games, with chapters that can run for hours.",
        "FGO follows Chaldea, an organization protecting human history, and Mash Kyrielight, your loyal shield-Servant companion, as you travel through Singularities to set things right.",
    ],
    "gacha_info": [
        "Summoning uses Saint Quartz! The total chance of a 5-star Servant is about 1% per pull. The good news: limited-time pickup banners have a Guaranteed Summon, so if you reach 330 summons without the featured 5-star, the 330th one is yours.",
        "You pull on rotating banners using Quartz or Summon Tickets. Pickup banners boost the featured Servants within that low 5-star rate, and on limited-time ones the featured 5-star is guaranteed by your 330th summon.",
        "Ehehe, gacha can be cruel~ 5-stars are roughly 1% per pull. But limited-time pickup banners have a 330-summon guarantee, which comes to about 900 Saint Quartz, so saving up for a Servant you really want is a solid plan.",
        "Each 11-summon costs 30 Saint Quartz and always includes a 4-star or better card. Just remember the 330-summon guarantee only covers limited-time pickup banners, not the permanent Story banner.",
    ],
    "gameplay_help": [
        "Combat's turn-based: each turn you pick 3 cards from your Servants' hands (Buster, Arts, or Quick), chain matching types for bonuses, and build your NP gauge for a big Noble Phantasm attack!",
        "Match class advantages (Saber beats Lancer, Lancer beats Archer, and so on) for extra damage, chain same-type cards for combo bonuses, and watch your NP gauge — hit 100% to unleash a Noble Phantasm.",
        "Mix Buster for damage, Arts for NP gauge, and Quick for critical stars. Pick three cards of the same color for a color chain bonus, or three cards from the same Servant for a Brave Chain and an extra attack!",
        "Pick your team wisely — a healer, a damage dealer, and good class matchups go a long way. Build up NP gauge through Arts cards or taking hits, then unleash your Noble Phantasm for a big finisher.",
    ],
    "event_info": [
        "Events usually run for a couple weeks and give bonus drops, a side story, and often free summons or a welfare Servant — definitely worth checking the event tab regularly!",
        "Limited-time events pop up often — story events, collabs, and anniversaries all bring unique rewards, sometimes including a free Servant just for participating.",
        "Keep an eye on the event tab! Most events offer a shop where you trade event currency for mats, plus a short story and sometimes a brand-new or returning Servant.",
        "Ehehe, there's almost always something going on — check in-game for the current banner and event schedule, since FGO rotates content pretty frequently.",
    ],
    "player_review": [
        "FGO's story is widely loved — some call it one of the best in mobile gaming — but the gacha is notoriously stingy and the combat can get grindy. Still very playable F2P if you're patient!",
        "Honestly? Worth it for the story alone if you like Fate lore. The gameplay loop is simple, the gacha is rough, but there's a reason people stick around for years.",
        "It's a mixed bag: incredible writing, so-so combat depth, and a gacha that tests your patience. F2P is doable, just don't expect to get every Servant you want right away.",
        "Long-time fans tend to agree the story carries the game — just go in knowing the gacha isn't generous, and pacing yourself matters more than spending.",
    ],
    "fallback_offtopic": [
        "Ehehe, that's a bit outside my wheelhouse~ I mainly know about FGO's story, servants, gacha, gameplay, and events!",
        "Mm, I'm not well versed in that topic — ask me something about FGO instead and I'll do my best!",
        "Fufu, that's not really my specialty. Try me on servants, gacha rates, or the story instead~",
    ],
    "fallback_unclear": [
        "Sorry, I didn't quite catch that — mind rephrasing?",
        "Hmm, not sure I followed — could you say that a different way?",
        "Ehehe, that one went over my head! Try asking again?",
    ],
}


def get_random_response(intent):
    """Return a random response string for the given intent key."""
    options = RESPONSES.get(intent)
    if not options:
        return "Hmm, I'm not sure how to answer that."
    return random.choice(options)
