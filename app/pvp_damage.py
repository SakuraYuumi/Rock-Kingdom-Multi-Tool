import json
import math
import sys
from pathlib import Path


PROJECT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
PVP_POKEMON_PATH = PROJECT_DIR / "data" / "pvp_pokemon_data.json"
PVP_SKILL_PATH = PROJECT_DIR / "data" / "pvp_skill_data.json"
PVP_FORMULA_PATH = PROJECT_DIR / "data" / "pvp_damage_formula.json"
PVP_TEAM_PATH = PROJECT_DIR / "data" / "pvp_team_slots.json"
PVP_CREATURE_SKILLS_PATH = PROJECT_DIR / "data" / "rocopvp_creature_skills.json"
PVP_ROCOPVP_CREATURES_PATH = PROJECT_DIR / "data" / "rocopvp_creatures.json"

STAT_LABELS = {
    "hp": "生命",
    "attack": "物攻",
    "defense": "物防",
    "special_attack": "魔攻",
    "special_defense": "魔防",
    "speed": "速度",
}

ATTRIBUTES = [
    "普通", "草", "火", "水", "光", "地", "冰", "龙", "电",
    "毒", "虫", "武", "翼", "萌", "幽", "恶", "机械", "幻",
]

TYPE_CHART = {
    "普通": {"普通": 1, "草": 1, "火": 1, "水": 1, "光": 1, "地": 0.5, "冰": 1, "龙": 1, "电": 1, "毒": 1, "虫": 1, "武": 1, "翼": 1, "萌": 1, "幽": 0.5, "恶": 1, "机械": 0.5, "幻": 1},
    "草": {"普通": 1, "草": 1, "火": 0.5, "水": 2, "光": 2, "地": 2, "冰": 1, "龙": 0.5, "电": 1, "毒": 0.5, "虫": 0.5, "武": 1, "翼": 0.5, "萌": 1, "幽": 1, "恶": 1, "机械": 0.5, "幻": 1},
    "火": {"普通": 1, "草": 2, "火": 1, "水": 0.5, "光": 1, "地": 0.5, "冰": 2, "龙": 0.5, "电": 1, "毒": 1, "虫": 2, "武": 1, "翼": 1, "萌": 1, "幽": 1, "恶": 1, "机械": 2, "幻": 1},
    "水": {"普通": 1, "草": 0.5, "火": 2, "水": 1, "光": 1, "地": 2, "冰": 0.5, "龙": 0.5, "电": 1, "毒": 1, "虫": 1, "武": 1, "翼": 1, "萌": 1, "幽": 1, "恶": 1, "机械": 2, "幻": 1},
    "光": {"普通": 1, "草": 0.5, "火": 1, "水": 1, "光": 1, "地": 1, "冰": 0.5, "龙": 1, "电": 1, "毒": 1, "虫": 1, "武": 1, "翼": 1, "萌": 1, "幽": 2, "恶": 2, "机械": 1, "幻": 1},
    "地": {"普通": 1, "草": 0.5, "火": 2, "水": 1, "光": 1, "地": 1, "冰": 2, "龙": 1, "电": 2, "毒": 2, "虫": 1, "武": 0.5, "翼": 1, "萌": 1, "幽": 1, "恶": 1, "机械": 1, "幻": 1},
    "冰": {"普通": 1, "草": 2, "火": 0.5, "水": 1, "光": 1, "地": 2, "冰": 0.5, "龙": 2, "电": 1, "毒": 1, "虫": 1, "武": 1, "翼": 2, "萌": 1, "幽": 1, "恶": 1, "机械": 0.5, "幻": 1},
    "龙": {"普通": 1, "草": 1, "火": 1, "水": 1, "光": 1, "地": 1, "冰": 1, "龙": 2, "电": 1, "毒": 1, "虫": 1, "武": 1, "翼": 1, "萌": 1, "幽": 1, "恶": 1, "机械": 0.5, "幻": 1},
    "电": {"普通": 1, "草": 0.5, "火": 1, "水": 2, "光": 1, "地": 0.5, "冰": 1, "龙": 0.5, "电": 0.5, "毒": 1, "虫": 1, "武": 1, "翼": 2, "萌": 1, "幽": 1, "恶": 1, "机械": 1, "幻": 1},
    "毒": {"普通": 1, "草": 2, "火": 1, "水": 1, "光": 1, "地": 0.5, "冰": 1, "龙": 1, "电": 1, "毒": 0.5, "虫": 1, "武": 1, "翼": 1, "萌": 2, "幽": 0.5, "恶": 1, "机械": 0.5, "幻": 1},
    "虫": {"普通": 1, "草": 2, "火": 0.5, "水": 1, "光": 1, "地": 1, "冰": 1, "龙": 1, "电": 1, "毒": 0.5, "虫": 1, "武": 0.5, "翼": 0.5, "萌": 0.5, "幽": 0.5, "恶": 2, "机械": 0.5, "幻": 2},
    "武": {"普通": 2, "草": 1, "火": 1, "水": 1, "光": 1, "地": 2, "冰": 2, "龙": 1, "电": 1, "毒": 0.5, "虫": 0.5, "武": 1, "翼": 0.5, "萌": 0.5, "幽": 0.5, "恶": 2, "机械": 2, "幻": 0.5},
    "翼": {"普通": 1, "草": 2, "火": 1, "水": 1, "光": 1, "地": 0.5, "冰": 1, "龙": 0.5, "电": 0.5, "毒": 1, "虫": 2, "武": 2, "翼": 1, "萌": 1, "幽": 1, "恶": 1, "机械": 0.5, "幻": 1},
    "萌": {"普通": 1, "草": 1, "火": 0.5, "水": 1, "光": 1, "地": 1, "冰": 1, "龙": 2, "电": 1, "毒": 0.5, "虫": 1, "武": 2, "翼": 1, "萌": 1, "幽": 1, "恶": 2, "机械": 0.5, "幻": 1},
    "幽": {"普通": 0.5, "草": 1, "火": 1, "水": 1, "光": 2, "地": 1, "冰": 1, "龙": 1, "电": 1, "毒": 1, "虫": 1, "武": 1, "翼": 1, "萌": 1, "幽": 2, "恶": 0.5, "机械": 1, "幻": 2},
    "恶": {"普通": 1, "草": 1, "火": 1, "水": 1, "光": 0.5, "地": 1, "冰": 1, "龙": 1, "电": 1, "毒": 2, "虫": 1, "武": 0.5, "翼": 1, "萌": 2, "幽": 2, "恶": 0.5, "机械": 1, "幻": 1},
    "机械": {"普通": 1, "草": 1, "火": 0.5, "水": 0.5, "光": 1, "地": 2, "冰": 2, "龙": 1, "电": 0.5, "毒": 1, "虫": 1, "武": 1, "翼": 1, "萌": 2, "幽": 1, "恶": 1, "机械": 0.5, "幻": 1},
    "幻": {"普通": 1, "草": 1, "火": 1, "水": 1, "光": 0.5, "地": 1, "冰": 1, "龙": 1, "电": 1, "毒": 2, "虫": 1, "武": 2, "翼": 1, "萌": 1, "幽": 1, "恶": 1, "机械": 0.5, "幻": 0.5},
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_pvp_pokemon():
    if not PVP_POKEMON_PATH.exists():
        return []
    payload = read_json(PVP_POKEMON_PATH)
    return payload.get("pokemon", []) if isinstance(payload, dict) else []


def load_pvp_skills():
    if not PVP_SKILL_PATH.exists():
        return []
    payload = read_json(PVP_SKILL_PATH)
    return payload.get("skills", []) if isinstance(payload, dict) else []


def load_pvp_formula():
    if not PVP_FORMULA_PATH.exists():
        return {
            "direct_damage": {
                "roco_constant": 37 / 41,
                "default_iv": 10,
            },
            "status_damage": {},
        }
    payload = read_json(PVP_FORMULA_PATH)
    return payload if isinstance(payload, dict) else {}


def load_pvp_creature_skills():
    if not PVP_CREATURE_SKILLS_PATH.exists():
        return {}
    payload = read_json(PVP_CREATURE_SKILLS_PATH)
    data = payload.get("creature_skills", {}) if isinstance(payload, dict) else {}
    return data if isinstance(data, dict) else {}


def load_rocopvp_creatures():
    if not PVP_ROCOPVP_CREATURES_PATH.exists():
        return []
    payload = read_json(PVP_ROCOPVP_CREATURES_PATH)
    data = payload.get("creatures", []) if isinstance(payload, dict) else []
    return data if isinstance(data, list) else []


def skills_for_creature(all_skills, creature, creature_skill_map=None, direct_only=True):
    if not creature:
        return list(all_skills)
    creature_skill_map = creature_skill_map or load_pvp_creature_skills()
    names = {
        str(item.get("name") or "")
        for item in creature_skill_map.get(str(creature.get("id") or ""), [])
    }
    if not names:
        result = list(all_skills)
    else:
        result = [skill for skill in all_skills if str(skill.get("name") or "") in names]
    if direct_only:
        result = [
            skill for skill in result
            if skill.get("power") is not None and skill.get("category") in {"物攻", "魔攻"}
        ]
    return result or list(all_skills)


def pokemon_key(item):
    if not isinstance(item, dict):
        return ""
    return "|".join(
        [
            str(item.get("id") or ""),
            str(item.get("t_id") or ""),
            str(item.get("name") or ""),
            "form" if item.get("is_form") else "base",
        ]
    )


def find_pokemon_by_key(pokemon, key):
    if not key:
        return None
    for item in pokemon:
        if pokemon_key(item) == key:
            return item
    # Backward-compatible fallback if older local data only stored names.
    for item in pokemon:
        if str(item.get("name") or "") == str(key):
            return item
    return None


def load_pvp_team():
    empty = {"attacker": [None] * 6, "defender": [None] * 6}
    if not PVP_TEAM_PATH.exists():
        return empty
    try:
        payload = read_json(PVP_TEAM_PATH)
    except Exception:
        return empty

    def normalize(slots):
        if not isinstance(slots, list):
            return [None] * 6
        normalized = []
        for slot in slots[:6]:
            normalized.append(str(slot) if slot else None)
        while len(normalized) < 6:
            normalized.append(None)
        return normalized

    if isinstance(payload, dict):
        if "attacker" in payload or "defender" in payload:
            return {
                "attacker": normalize(payload.get("attacker")),
                "defender": normalize(payload.get("defender")),
            }
        if "slots" in payload:
            return {"attacker": normalize(payload.get("slots")), "defender": [None] * 6}
    if isinstance(payload, list):
        return {"attacker": normalize(payload), "defender": [None] * 6}
    return empty


def save_pvp_team(slots):
    def normalize(value):
        normalized = []
        for slot in list(value or [])[:6]:
            normalized.append(str(slot) if slot else None)
        while len(normalized) < 6:
            normalized.append(None)
        return normalized

    if isinstance(slots, dict):
        payload = {
            "version": 2,
            "attacker": normalize(slots.get("attacker")),
            "defender": normalize(slots.get("defender")),
        }
    else:
        payload = {
            "version": 2,
            "attacker": normalize(slots),
            "defender": [None] * 6,
        }
    write_json(PVP_TEAM_PATH, payload)


def number(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _js_round(value):
    if not math.isfinite(value):
        return 0
    if value >= 0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))


def _roco_inner_round(value, iv):
    floored = math.floor(value)
    is_half = abs(value - floored - 0.5) < (
        math.ulp(1.0) * max(100.0, abs(value))
    )
    if int(iv) == 0 and is_half:
        return floored + 1 if floored % 2 == 0 else floored
    return _js_round(value)


def calculate_derived_stat(kind, base, iv=10, nature="neutral"):
    iv = max(0, min(10, int(round(number(iv, 10)))))
    nature_multiplier = {"boost": 1.2, "drop": 0.9}.get(str(nature), 1.0)
    base_value = number(base)
    if kind == "hp":
        inner = _roco_inner_round(1.7 * (base_value + 3 * iv), iv) + 70
        return _js_round(inner * nature_multiplier) + 100
    inner = _roco_inner_round(1.1 * (base_value + 3 * iv), iv) + 10
    return _js_round(inner * nature_multiplier) + 50


def _stat_config_for(stat, config):
    config = config or {}
    ivs = config.get("ivs") if isinstance(config.get("ivs"), dict) else {}
    iv = ivs.get(stat, config.get("iv", config.get("default_iv", 10)))
    if config.get("boosted_stat") == stat:
        nature = "boost"
    elif config.get("dropped_stat") == stat:
        nature = "drop"
    else:
        nature = "neutral"
    return iv, nature


def derived_stats(creature, config=None):
    mapping = {}
    for stat in STAT_LABELS:
        iv, nature = _stat_config_for(stat, config)
        mapping[stat] = calculate_derived_stat(stat, creature.get(stat), iv, nature)
    return mapping


def percent_ability_multiplier(attack_percent, defense_percent):
    attack_percent = number(attack_percent)
    defense_percent = number(defense_percent)
    numerator = 1.0 + max(attack_percent, 0.0) / 100.0 + max(-defense_percent, 0.0) / 100.0
    denominator = 1.0 + max(-attack_percent, 0.0) / 100.0 + max(defense_percent, 0.0) / 100.0
    return numerator / max(denominator, 0.0001)


def reduction_multiplier(percent):
    return max(0.0, 1.0 - number(percent) / 100.0)


def damage_multiplier(percent):
    return max(0.0, min(4.0, 1.0 + number(percent) / 100.0))


def type_multiplier_for(attack_attribute, defender_attributes):
    attack_attribute = str(attack_attribute or "")
    if attack_attribute not in TYPE_CHART:
        return 1.0
    values = [
        TYPE_CHART[attack_attribute].get(str(attr), 1.0)
        for attr in (defender_attributes or [])
        if str(attr) in ATTRIBUTES
    ]
    if not values:
        return 1.0
    if len(values) == 1:
        return values[0]
    has_strong = any(value > 1 for value in values)
    has_resist = any(value < 1 for value in values)
    if has_strong and has_resist:
        return 1.0
    if all(value > 1 for value in values):
        return 3.0
    if all(value < 1 for value in values):
        return 0.25
    result = 1.0
    for value in values:
        result *= value
    return result


def direct_damage_stats(attacker, defender, skill, options=None):
    options = options or {}
    category = str(skill.get("category") or "")
    attacker_config = options.get("attacker_stat_config")
    defender_config = options.get("defender_stat_config")
    attacker_stats = derived_stats(attacker, attacker_config)
    defender_stats = derived_stats(defender, defender_config)
    if category == "物攻":
        attack_key, defense_key = "attack", "defense"
    elif category == "魔攻":
        attack_key, defense_key = "special_attack", "special_defense"
    else:
        attack_key, defense_key = "", ""
    return {
        "category": category,
        "attack_stat_key": attack_key,
        "defense_stat_key": defense_key,
        "attack_stat_name": STAT_LABELS.get(attack_key, ""),
        "defense_stat_name": STAT_LABELS.get(defense_key, ""),
        "attack_stat": attacker_stats.get(attack_key, 0),
        "defense_stat": defender_stats.get(defense_key, 0),
        "attacker_panel": attacker_stats,
        "defender_panel": defender_stats,
    }


def has_stab(attacker, skill):
    attr = str(skill.get("attribute") or "")
    return bool(attr and attr in (attacker.get("attributes") or []))


def calculate_battle_damage(
    attacker_stat,
    display_power,
    defender_defense,
    damage_reduction_multiplier=1.0,
    hit_count=1,
    roco_constant=37 / 41,
):
    if attacker_stat <= 0 or display_power <= 0 or defender_defense <= 0:
        return 0
    inner = (
        attacker_stat
        * display_power
        * max(damage_reduction_multiplier, 0.0)
        * max(int(hit_count), 1)
        * number(roco_constant, 37 / 41)
    )
    return int(math.floor(_js_round(inner) / defender_defense))


def calculate_pvp_damage(attacker, defender, skill, options=None, formula=None):
    options = options or {}
    formula = formula or load_pvp_formula()
    direct_formula = formula.get("direct_damage", {}) if isinstance(formula, dict) else {}
    power = skill.get("power")
    if power is None:
        return {
            "ok": False,
            "damage": 0,
            "message": "这个技能没有直伤威力，暂不计算伤害。",
        }

    stats = direct_damage_stats(attacker, defender, skill, options)
    if stats["category"] not in {"物攻", "魔攻"}:
        return {
            "ok": False,
            "damage": 0,
            "message": "当前只计算物攻/魔攻直伤技能。",
        }

    roco_constant = number(direct_formula.get("roco_constant"), 37 / 41)
    type_multiplier = max(0.0, number(options.get("type_multiplier"), 1.0))
    hit_count = max(1, int(number(options.get("hit_count"), 1)))
    misc_multiplier = max(0.0, number(options.get("misc_multiplier"), 1.0))
    power_bonus = number(
        options.get("power_bonus", options.get("power_modifier_percent", 0.0))
    )
    attack_modifier = number(options.get("attack_modifier_percent", 0.0))
    defense_modifier = number(options.get("defense_modifier_percent", 0.0))
    ability_multiplier = percent_ability_multiplier(attack_modifier, defense_modifier)
    reduction = reduction_multiplier(options.get("reduction_percent", 0.0))
    extra_damage = damage_multiplier(options.get("damage_modifier_percent", 0.0))
    stab_multiplier = 1.0
    if options.get("auto_stab", True):
        stab_multiplier = 1.25 if has_stab(attacker, skill) else 1.0
    if options.get("stab_multiplier") is not None:
        stab_multiplier = max(0.0, number(options.get("stab_multiplier"), stab_multiplier))

    effective_power = max(0.0, number(power) + power_bonus)
    display_power_raw = (
        effective_power
        * stab_multiplier
        * type_multiplier
        * misc_multiplier
        * ability_multiplier
    )
    display_power = _js_round(display_power_raw)
    base_damage = calculate_battle_damage(
        stats["attack_stat"],
        display_power,
        stats["defense_stat"],
        reduction,
        hit_count,
        roco_constant,
    )
    total_damage = int(math.floor(max(0.0, base_damage * extra_damage)))
    single_damage = calculate_battle_damage(
        stats["attack_stat"],
        display_power,
        stats["defense_stat"],
        reduction,
        1,
        roco_constant,
    )
    defender_hp = max(1.0, number(stats["defender_panel"].get("hp"), 1.0))

    return {
        "ok": True,
        "damage": total_damage,
        "single_damage": single_damage,
        "base_damage_before_extra": base_damage,
        "hp_percent": total_damage / defender_hp * 100.0,
        "hit_count": hit_count,
        "message": "计算成功",
        "details": {
            **stats,
            "skill_power": number(power),
            "effective_power": effective_power,
            "display_power_raw": display_power_raw,
            "display_power": display_power,
            "type_multiplier": type_multiplier,
            "stab_multiplier": stab_multiplier,
            "misc_multiplier": misc_multiplier,
            "attack_modifier_percent": attack_modifier,
            "defense_modifier_percent": defense_modifier,
            "ability_multiplier": ability_multiplier,
            "reduction_modifier": reduction,
            "damage_modifier": extra_damage,
            "roco_constant": roco_constant,
        },
    }


def _status_definitions(formula=None):
    formula = formula or load_pvp_formula()
    payload = formula.get("status_damage", {}) if isinstance(formula, dict) else {}
    defaults = {
        "burn": {
            "label": "灼烧",
            "rate": 0.02,
            "hp_cap": 1000,
            "kind": "damage",
            "type_multiplier_option": "burn_type_multiplier",
            "note": "按最大生命结算，默认按 1000 血封顶，可手动填克制倍率。",
        },
        "poison": {
            "label": "中毒",
            "rate": 0.03,
            "hp_cap": None,
            "kind": "damage",
            "note": "按最大生命结算。",
        },
        "leech": {
            "label": "寄生",
            "rate": 0.06,
            "hp_cap": None,
            "kind": "drain",
            "note": "按最大生命吸取，并回复同等生命。",
        },
        "freeze": {
            "label": "冻结",
            "rate": 0.05,
            "hp_cap": None,
            "kind": "threshold",
            "note": "冻结不是直接扣血，这里显示被锁定的生命阈值。",
        },
    }
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, dict) and key in defaults:
                defaults[key] = {**defaults[key], **value}
    return defaults


def calculate_status_effects(defender, options=None, formula=None):
    options = options or {}
    defender_config = options.get("defender_stat_config")
    defender_hp = derived_stats(defender, defender_config)["hp"]
    definitions = _status_definitions(formula)
    rows = []
    total_damage = 0
    total_heal = 0
    for key, definition in definitions.items():
        stacks = max(0, int(number(options.get(f"{key}_stacks"), 0)))
        if stacks <= 0:
            continue
        hp_cap = definition.get("hp_cap")
        base_hp = min(defender_hp, number(hp_cap)) if hp_cap else defender_hp
        multiplier = 1.0
        type_option = definition.get("type_multiplier_option")
        if type_option:
            multiplier = max(0.0, number(options.get(type_option), 1.0))
        raw_value = base_hp * number(definition.get("rate")) * stacks * multiplier
        value = int(math.floor(max(0.0, raw_value)))
        kind = definition.get("kind", "damage")
        row = {
            "key": key,
            "label": definition.get("label", key),
            "kind": kind,
            "stacks": stacks,
            "rate": number(definition.get("rate")),
            "base_hp": base_hp,
            "multiplier": multiplier,
            "value": value,
            "raw_value": raw_value,
            "note": definition.get("note", ""),
        }
        if kind in {"damage", "drain"}:
            total_damage += value
        if kind == "drain":
            total_heal += value
        rows.append(row)
    return {
        "defender_hp": defender_hp,
        "rows": rows,
        "total_damage": total_damage,
        "total_heal": total_heal,
    }


def item_label(item):
    t_id = str(item.get("t_id") or "").strip()
    name = str(item.get("name") or "").strip()
    return f"No.{t_id} {name}" if t_id else name
