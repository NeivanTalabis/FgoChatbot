import random
import re

CLASS_FLAVOR = {
    "saber": "a blade-wielding Saber",
    "archer": "a sharp-eyed Archer",
    "lancer": "a swift Lancer",
    "rider": "a Rider who commands beasts or vehicles",
    "caster": "a spellcasting Caster",
    "assassin": "a shadowy Assassin",
    "berserker": "a ferocious Berserker",
    "ruler": "a rule-bound Ruler",
    "avenger": "a vengeful Avenger",
    "moonCancer": "a mysterious Moon Cancer",
    "alterEgo": "an Alter Ego",
    "foreigner": "an otherworldly Foreigner",
    "pretender": "a deceptive Pretender",
    "shielder": "a stalwart Shielder",
    "beast": "a Beast-class existence",
}

ATTRIBUTE_NAMES = {
    "human": "Man",
    "sky": "Sky",
    "earth": "Earth",
    "star": "Star",
    "beast": "Beast",
}

TRAIT_LABELS = {
    "king": "King",
    "divine": "Divine",
    "dragon": "Dragon",
    "demonic": "Demonic",
    "undead": "Undead",
    "riding": "Riding",
    "humanoid": "Humanoid",
    "brynhildsBeloved": "Brynhild's Beloved",
}

ALIGNMENT_ORDER = {"lawful": 0, "neutral": 1, "chaotic": 2}

INTROS = [
    "Ehehe, you're curious about {name}? Let me tell you~",
    "Oh-ho, {name}! Good choice. Here's the scoop:",
    "Fufu, {name} huh? I like your taste!",
    "Mm, {name}... a fine pick, Master.",
]

CLASS_LINES = [
    "They fight as {flavor}, rarity {rarity} stars.",
    "Rarity {rarity} stars, and they're {flavor}.",
    "A {rarity}-star hero, fighting as {flavor}.",
]

PROFILE_LINES = [
    "By alignment they're {alignment}, with the {attribute} attribute.",
    "{alignment} in alignment, and {attribute} attribute.",
]

TRAIT_LINES = [
    "Notable traits: {traits}.",
    "Traits worth knowing: {traits}.",
]

STAT_LINES = [
    "At max level they reach {atk} ATK and {hp} HP.",
    "Max-level stats: {atk} ATK and {hp} HP.",
]

OUTROS = [
    "Want to know about another servant? Just ask~",
    "There's always more to learn about our fellow heroic spirits!",
    "Chaldea's full of interesting company, isn't it?",
]


def pretty_class(class_name):
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", class_name or "")
    return " ".join(word.capitalize() for word in spaced.split())


def _split_camel(text):
    return re.sub(r"(?<!^)(?=[A-Z])", " ", text)


def get_alignment(servant):
    parts = []
    for trait in servant.get("traits", []):
        name = trait.get("name", "")
        if name.startswith("alignment") and len(name) > len("alignment"):
            parts.append(_split_camel(name[len("alignment"):]))
    if not parts:
        return None
    parts.sort(key=lambda p: (ALIGNMENT_ORDER.get(p.lower(), 3), p))
    return " ".join(parts)


def get_traits(servant, limit=4):
    present = {t.get("name") for t in servant.get("traits", [])}
    return [label for key, label in TRAIT_LABELS.items() if key in present][:limit]


def describe_servant(servant):
    name = servant.get("name", "this servant")
    class_name = servant.get("className", "")
    rarity = servant.get("rarity", "?")
    flavor = CLASS_FLAVOR.get(class_name, f"a {pretty_class(class_name)}-class servant")

    parts = [
        random.choice(INTROS).format(name=name),
        random.choice(CLASS_LINES).format(flavor=flavor, rarity=rarity),
    ]

    alignment = get_alignment(servant)
    attribute = ATTRIBUTE_NAMES.get(servant.get("attribute", ""), servant.get("attribute", "").capitalize())
    if alignment and attribute:
        parts.append(random.choice(PROFILE_LINES).format(alignment=alignment, attribute=attribute))
    elif alignment:
        parts.append(f"By alignment they're {alignment}.")
    elif attribute:
        parts.append(f"They have the {attribute} attribute.")

    traits = get_traits(servant)
    if traits:
        parts.append(random.choice(TRAIT_LINES).format(traits=", ".join(traits)))

    atk, hp = servant.get("atkMax"), servant.get("hpMax")
    if atk and hp:
        parts.append(random.choice(STAT_LINES).format(atk=f"{atk:,}", hp=f"{hp:,}"))

    other_forms = servant.get("_other_forms")
    if other_forms:
        forms = ", ".join(
            f"{pretty_class(f.get('className', ''))} ({f.get('rarity', '?')}-star)"
            for f in other_forms[:3]
        )
        if len(other_forms) == 1:
            parts.append(f"Heads up, they have another version too: {forms}.")
        else:
            parts.append(f"Heads up, they have other versions too: {forms}.")

    similar = servant.get("_similar_names")
    if similar:
        parts.append(
            f"There are other servants who share that name too, like {', '.join(similar)} "
            "- ask for them by full name if you meant someone else!"
        )

    parts.append(random.choice(OUTROS))
    return " ".join(parts)


def generic_servant_reply():
    return (
        "Ehehe, ask me about a specific servant by name and I'll tell you "
        "what I know about their class, rarity, and stats~ Try someone like Gilgamesh, "
        "Cu Chulainn, or Nero!"
    )

CLASS_NOTES = {
    "saber": "Sabers deal double damage to Lancers, but take double damage from Archers.",
    "archer": "Archers deal double damage to Sabers, but take double damage from Lancers.",
    "lancer": "Lancers deal double damage to Archers, but take double damage from Sabers.",
    "rider": "Riders deal double damage to Casters, but take double damage from Assassins.",
    "caster": "Casters deal double damage to Assassins, but take double damage from Riders.",
    "assassin": "Assassins deal double damage to Riders, but take double damage from Casters.",
    "berserker": "Berserkers deal 1.5x damage to nearly every class, but take double damage in return.",
    "ruler": "Rulers take half damage from every class except Berserkers.",
    "shielder": "Shielders deal and take normal damage against every class.",
}

CLASS_INTROS = [
    "Ehehe, the {label} class? Let me tell you~",
    "Oh-ho, {label}! Good choice. Here's the scoop:",
    "Fufu, {label}... a fine class to ask about, Master.",
]

CLASS_BLURBS = {
    "saber": "one of the three knight classes, built around the sword",
    "archer": "one of the three knight classes, usually fighting from range",
    "lancer": "one of the three knight classes, wielding spears",
    "rider": "the class of heroes who ride mounts and vehicles",
    "caster": "the class of spellcasters",
    "assassin": "the class of stealthy killers",
    "berserker": "the class that gives up reason for raw power",
    "ruler": "one of the special 'extra' classes",
    "shielder": "one of the special 'extra' classes",
}
EXTRA_CLASS_BLURB = "one of the special 'extra' classes"


def describe_class(class_key, count, examples):
    label = pretty_class(class_key)
    parts = [
        random.choice(CLASS_INTROS).format(label=label),
        f"{label} is {CLASS_BLURBS.get(class_key, EXTRA_CLASS_BLURB)}.",
    ]
    if class_key in CLASS_NOTES:
        parts.append(CLASS_NOTES[class_key])
    if count:
        verb, noun = ("is", "servant") if count == 1 else ("are", "servants")
        parts.append(f"There {verb} {count} {label}-class {noun} in my records, like {', '.join(examples)}.")
    parts.append("Ask me about any of them by name!")
    return " ".join(parts)


def classes_overview_reply():
    return (
        "Ehehe, servants fight under classes! The seven standard ones are Saber, Archer, Lancer, "
        "Rider, Caster, Assassin and Berserker, plus special 'extra' classes like Ruler, Avenger, "
        "Moon Cancer, Alter Ego, Foreigner, Pretender, Shielder and Beast. Saber beats Lancer, "
        "Lancer beats Archer and Archer beats Saber; Rider beats Caster, Caster beats Assassin "
        "and Assassin beats Rider; Berserkers hit everything hard but take double damage. "
        "Ask me about one class, like Saber, and I'll tell you more~"
    )
