#!/usr/bin/env python3
"""Build recipe-nutrient-data.js from recipe nutrient panels plus estimated backfill.

Panel values remain authoritative. If one of the target nutrients is missing
for a recipe card (choline, omega3, folate, b12), this script backfills it
from card ingredients using the same heuristic profile used in recipes.html.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RECIPES_DIR = ROOT / "recipes"
RECIPES_HTML = ROOT / "recipes.html"
OUTPUT_JS = ROOT / "recipe-nutrient-data.js"

TARGET_KEYS = ("choline", "omega3", "folate", "b12")


def strip_html(value: str) -> str:
    return re.sub(r"<.*?>", "", value, flags=re.S).strip()


def normalize_ingredient(part: str) -> str:
    value = re.sub(r"\s+", " ", part or "").strip().lower()
    value = re.sub(r"\([^)]*\)", "", value)
    value = value.replace("extra virgin olive oil", "evoo")
    value = value.replace("olive oil", "evoo")
    value = value.replace("omega 3", "omega-3")
    value = value.replace("omega3", "omega-3")
    return re.sub(r"\s+", " ", value).strip()


def estimate_targets_from_ingredients(ingredients_text: str) -> dict[str, float]:
    tokens = [normalize_ingredient(p) for p in (ingredients_text or "").split("\u22c5")]
    unique_tokens = [t for t in dict.fromkeys(tokens) if t]

    totals = {
        "cholineMg": 0.0,
        "omega3Mg": 0.0,
        "folateMcg": 0.0,
        "b12Mcg": 0.0,
    }

    def has(token: str, terms: list[str]) -> bool:
        return any(term in token for term in terms)

    for token in unique_tokens:
        # Choline (mg)
        if has(token, ["liver"]):
            totals["cholineMg"] += 280
        elif has(token, ["eggs", "egg"]):
            totals["cholineMg"] += 145
        elif has(token, ["salmon", "sardine", "mackerel", "shrimp", "crab", "oyster"]):
            totals["cholineMg"] += 95
        elif has(token, ["chicken", "turkey", "beef", "pork"]):
            totals["cholineMg"] += 80
        elif has(token, ["yogurt", "kefir", "milk", "mozzarella", "feta", "parmesan"]):
            totals["cholineMg"] += 30
        elif has(token, ["beans", "lentils", "broccoli"]):
            totals["cholineMg"] += 25

        # Omega-3 (mg)
        if has(token, ["salmon"]):
            totals["omega3Mg"] += 1800
        elif has(token, ["sardine", "mackerel"]):
            totals["omega3Mg"] += 1500
        elif has(token, ["oyster", "shrimp", "crab"]):
            totals["omega3Mg"] += 250
        elif has(token, ["walnut"]):
            totals["omega3Mg"] += 650
        elif has(token, ["chia"]):
            totals["omega3Mg"] += 900
        elif has(token, ["flax"]):
            totals["omega3Mg"] += 700
        elif has(token, ["hemp"]):
            totals["omega3Mg"] += 350

        # Folate (mcg)
        if has(token, ["spinach", "parsley", "asparagus", "lentils"]):
            totals["folateMcg"] += 80
        elif has(token, ["kale", "beans", "broccoli", "avocado"]):
            totals["folateMcg"] += 50
        elif has(token, ["cabbage", "bell pepper", "tomatoes", "zucchini", "cucumber"]):
            totals["folateMcg"] += 20

        # B12 (mcg)
        if has(token, ["liver"]):
            totals["b12Mcg"] += 8.0
        elif has(token, ["mackerel", "sardine", "salmon"]):
            totals["b12Mcg"] += 2.8
        elif has(token, ["beef", "shrimp", "crab", "oyster"]):
            totals["b12Mcg"] += 2.2
        elif has(token, ["chicken", "turkey", "pork"]):
            totals["b12Mcg"] += 0.7
        elif has(token, ["eggs", "egg"]):
            totals["b12Mcg"] += 0.6
        elif has(token, ["yogurt", "kefir", "milk", "mozzarella", "feta", "parmesan"]):
            totals["b12Mcg"] += 0.4

    totals["cholineMg"] = min(totals["cholineMg"], 420)
    totals["omega3Mg"] = min(totals["omega3Mg"], 2500)
    totals["folateMcg"] = min(totals["folateMcg"], 320)
    totals["b12Mcg"] = min(totals["b12Mcg"], 10)

    return {
        "cholineMg": round(totals["cholineMg"]),
        "omega3Mg": round(totals["omega3Mg"]),
        "folateMcg": round(totals["folateMcg"]),
        "b12Mcg": round(totals["b12Mcg"], 1),
    }


def parse_unit(amount_text: str) -> str | None:
    low = amount_text.lower().replace("μg", "ug").replace("µg", "ug")
    if re.search(r"\bug\b", low) or "mcg" in low:
        return "mcg"
    if re.search(r"\bmg\b", low):
        return "mg"
    if re.search(r"\bg\b", low):
        return "g"
    return None


def convert_to_canonical(value: float, from_unit: str | None, key: str) -> tuple[float, str]:
    # Canonical planner units: choline/omega3 mg, folate/b12 mcg.
    if key in ("choline", "omega3"):
        if from_unit == "g":
            return value * 1000.0, "mg"
        if from_unit == "mcg":
            return value / 1000.0, "mg"
        return value, "mg"
    if key in ("folate", "b12"):
        if from_unit == "g":
            return value * 1_000_000.0, "mcg"
        if from_unit == "mg":
            return value * 1000.0, "mcg"
        return value, "mcg"
    return value, from_unit or ""


def key_for_nutrient_name(name_text: str) -> str | None:
    lname = name_text.lower()
    if "choline" in lname:
        return "choline"
    if "omega-3" in lname or "omega 3" in lname or "epa" in lname or "dha" in lname:
        return "omega3"
    if "folate" in lname:
        return "folate"
    if "b12" in lname or "vitamin b12" in lname:
        return "b12"
    return None


def parse_panel_target_data(recipe_html: str) -> dict[str, dict[str, object]]:
    pairs = re.findall(
        r"<span\s+class=\"nutr-name\"[^>]*>(.*?)</span>\s*<span\s+class=\"nutr-amount\"[^>]*>(.*?)</span>",
        recipe_html,
        flags=re.S,
    )

    out: dict[str, dict[str, object]] = {}
    for raw_name, raw_amount in pairs:
        name = strip_html(raw_name)
        amount = strip_html(raw_amount)
        key = key_for_nutrient_name(name)
        if not key:
            continue

        nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", amount.replace(",", ""))]
        if not nums:
            continue

        average = sum(nums) / len(nums)
        unit = parse_unit(amount)
        canonical_value, canonical_unit = convert_to_canonical(average, unit, key)
        out[key] = {
            "display": amount,
            "value": canonical_value,
            "unit": canonical_unit,
            "name": name,
            "estimated": False,
        }

    return out


def parse_recipe_cards(recipes_html: str) -> list[dict[str, str]]:
    cards = re.findall(
        r"<div class=\"recipe-card\"[\s\S]*?<div class=\"recipe-card-footer\">[\s\S]*?</div>\s*</div>",
        recipes_html,
    )
    parsed = []
    for card in cards:
        href_match = re.search(r'href=\"(recipes/[^\"]+\.html)\"', card)
        ing_match = re.search(r"<p class=\"recipe-card-ingredients\">(.*?)</p>", card, flags=re.S)
        title_match = re.search(r"<div class=\"recipe-card-title\">(.*?)</div>", card, flags=re.S)
        if not href_match:
            continue
        parsed.append(
            {
                "href": href_match.group(1),
                "file": href_match.group(1).split("/")[-1],
                "ingredients": strip_html(ing_match.group(1)) if ing_match else "",
                "title": strip_html(title_match.group(1)) if title_match else href_match.group(1),
            }
        )
    return parsed


def build_entry_with_backfill(panel_entry: dict[str, dict[str, object]], estimates: dict[str, float]) -> dict[str, dict[str, object]]:
    entry: dict[str, dict[str, object]] = dict(panel_entry)

    estimate_map = {
        "choline": (estimates["cholineMg"], "mg", "Choline (estimated)"),
        "omega3": (estimates["omega3Mg"], "mg", "Omega-3 (estimated)"),
        "folate": (estimates["folateMcg"], "mcg", "Folate (estimated)"),
        "b12": (estimates["b12Mcg"], "mcg", "B12 (estimated)"),
    }

    for key, (value, unit, name) in estimate_map.items():
        if key in entry and entry[key].get("value") is not None:
            continue
        decimals = 1 if key == "b12" else 0
        rounded = round(float(value), decimals)
        if decimals == 0:
            rounded = int(rounded)
        entry[key] = {
            "display": f"~{rounded} {unit} (estimated)",
            "value": float(rounded),
            "unit": unit,
            "name": name,
            "estimated": True,
        }

    return entry


def main() -> None:
    recipes_html_text = RECIPES_HTML.read_text()

    # 1) Parse panel data from each recipe page.
    panel_map: dict[str, dict[str, dict[str, object]]] = {}
    for path in sorted(RECIPES_DIR.glob("*.html")):
        panel_map[path.name] = parse_panel_target_data(path.read_text())

    # 2) For each card in recipes.html, ensure all 4 target nutrients exist.
    final_map: dict[str, dict[str, dict[str, object]]] = {}
    cards = parse_recipe_cards(recipes_html_text)
    estimated_backfills = 0

    for card in cards:
        file_name = card["file"]
        base_panel = panel_map.get(file_name, {})
        est = estimate_targets_from_ingredients(card["ingredients"])
        merged = build_entry_with_backfill(base_panel, est)
        estimated_backfills += sum(1 for key in TARGET_KEYS if merged[key].get("estimated"))
        final_map[file_name] = merged

    # 3) Preserve parsed nutrient data for recipe files that are not card-linked.
    for file_name, nutrients in panel_map.items():
        final_map.setdefault(file_name, nutrients)

    js = "window.RECIPE_PANEL_NUTRIENTS = " + json.dumps(final_map, indent=2, ensure_ascii=False) + ";\n"
    OUTPUT_JS.write_text(js)

    card_count = len(cards)
    all4_count = sum(
        1
        for card in cards
        if all(
            final_map.get(card["file"], {}).get(key, {}).get("value") is not None
            for key in TARGET_KEYS
        )
    )

    print(f"Wrote {OUTPUT_JS}")
    print(f"Card-linked recipes: {card_count}")
    print(f"Card-linked recipes with all 4 targets: {all4_count}")
    print(f"Estimated target backfills applied: {estimated_backfills}")


if __name__ == "__main__":
    main()
