"""Offline, rule-based travel itinerary planner."""

from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path
import re
from typing import Any


DATA_FILE = Path(__file__).with_name("destinations.json")
DESTINATIONS: dict[str, Any] = json.loads(DATA_FILE.read_text(encoding="utf-8"))

INTERESTS = ["culture", "history", "food", "nature", "art", "shopping", "relaxation", "adventure"]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _date_label(start: str, day_index: int) -> str:
    if not start:
        return f"Day {day_index + 1}"
    try:
        day = date.fromisoformat(start) + timedelta(days=day_index)
        return day.strftime("%a, %b ") + str(day.day)
    except (ValueError, TypeError):
        return f"Day {day_index + 1}"


def _fallback_places(destination: str, interests: list[str]) -> list[dict[str, Any]]:
    """Offer useful neighborhood/activity prompts without inventing venue names."""
    labels = {
        "culture": ("Local cultural quarter", "Explore a neighborhood known for local life, architecture, and community spaces."),
        "history": ("Historic center walk", "Walk the old town or civic center; choose a landmark and a nearby history museum."),
        "food": ("Market and local food trail", "Visit a public market, then try a well-reviewed local specialty nearby."),
        "nature": ("City park or waterfront", "Spend time in a major public garden, riverside path, or waterfront promenade."),
        "art": ("Art museum or gallery district", "Pick a major collection or independent gallery cluster and leave time for a café stop."),
        "shopping": ("Independent shops and local market", "Browse a walkable shopping street or craft market; check opening days first."),
        "relaxation": ("Slow morning and scenic café", "Keep the morning flexible, then choose a nearby garden, spa, or quiet café."),
        "adventure": ("Active outdoor half-day", "Look for a reputable guided hike, cycle route, or water activity suited to the season."),
    }
    chosen = list(dict.fromkeys(interests or ["culture", "food", "nature", "history", "art"]))
    result = []
    for interest in chosen:
        name, description = labels[interest]
        result.append({"name": name, "area": destination, "description": description, "tags": [interest], "duration": 2.0, "cost": 0})
    result += [
        {"name": "Neighborhood discovery", "area": destination, "description": "Choose a walkable district and explore at an unhurried pace.", "tags": ["culture", "food"], "duration": 2.0, "cost": 0},
        {"name": "Free viewpoint or public space", "area": destination, "description": "Find a public viewpoint, plaza, or waterfront for a low-cost change of pace.", "tags": ["nature", "relaxation"], "duration": 1.5, "cost": 0},
    ]
    return result


def _budget_level(per_person_day: float, currency: str) -> str:
    # Approximate tiers in each supported currency (roughly value/balanced/comfort).
    thresholds = {
        "USD": (75, 200), "EUR": (70, 185), "GBP": (60, 160),
        "INR": (4000, 12000), "CAD": (100, 270), "AUD": (110, 300), "JPY": (11000, 30000),
    }
    low, high = thresholds.get(currency, (75, 200))
    if per_person_day < low:
        return "value"
    if per_person_day < high:
        return "balanced"
    return "comfort"


def _select_day(places: list[dict[str, Any]], interests: list[str], level: str, pace: str, used: set[str]) -> list[dict[str, Any]]:
    limits = {"relaxed": 2, "balanced": 3, "packed": 4}
    time_limits = {"relaxed": 5, "balanced": 7, "packed": 9}
    candidates = [p for p in places if p["name"] not in used]

    def score(place: dict[str, Any]) -> float:
        interest_score = sum(1 for tag in place["tags"] if tag in interests) * 5
        price = place["cost"]
        price_score = (3 if price <= 15 else 1 if price <= 40 else -3) if level == "value" else (2 if price <= 40 else 0 if price <= 90 else -2) if level == "balanced" else (0 if price <= 90 else 2)
        return interest_score + price_score + (1 if place["duration"] <= 2.5 else 0)

    candidates.sort(key=score, reverse=True)
    day: list[dict[str, Any]] = []
    total_time = 0.0
    for place in candidates:
        if len(day) >= limits[pace] or total_time + place["duration"] > time_limits[pace]:
            continue
        day.append(place)
        used.add(place["name"])
        total_time += place["duration"]
    if not day:
        day = [candidates[0]] if candidates else []
        if day:
            used.add(day[0]["name"])
    return day


def make_plan(data: dict[str, Any]) -> dict[str, Any]:
    destination = str(data.get("destination", "")).strip()
    if not destination:
        raise ValueError("Enter a destination to build your plan.")
    try:
        days = int(data.get("days", 4))
        travelers = int(data.get("travelers", 1))
        budget = float(data.get("budget", 1000))
    except (TypeError, ValueError):
        raise ValueError("Days, travelers, and budget must be valid numbers.") from None
    if not 1 <= days <= 14:
        raise ValueError("Choose a trip length from 1 to 14 days.")
    if not 1 <= travelers <= 20:
        raise ValueError("Choose between 1 and 20 travelers.")
    if budget < 0:
        raise ValueError("Budget cannot be negative.")

    interests = [str(i).lower() for i in data.get("interests", []) if str(i).lower() in INTERESTS]
    if not interests:
        interests = ["culture", "food", "history"]
    pace = data.get("pace", "balanced")
    if pace not in {"relaxed", "balanced", "packed"}:
        pace = "balanced"
    currency = str(data.get("currency", "USD"))[:5].upper()
    per_person_day = budget / travelers / days if travelers and days else 0
    level = _budget_level(per_person_day, currency)
    key = slug(destination)
    matched = next((v for k, v in DESTINATIONS.items() if slug(k) == key), None)
    catalog = matched["places"] if matched else _fallback_places(destination, interests)
    # Normalize and rank a fresh pool each day, so shorter lists can be revisited thoughtfully.
    places = [dict(p) for p in catalog]
    schedule = []
    used: set[str] = set()
    for idx in range(days):
        desired_count = {"relaxed": 2, "balanced": 3, "packed": 4}[pace]
        if idx and len(places) - len(used) < desired_count:
            used.clear()
        day_places = _select_day(places, interests, level, pace, used)
        slots = ["Morning", "Afternoon", "Evening", "Flexible"]
        activities = []
        for j, p in enumerate(day_places):
            activities.append({**p, "slot": slots[min(j, len(slots) - 1)]})
        schedule.append({"label": _date_label(str(data.get("start_date", "")), idx), "activities": activities})

    # Planning estimates only: daily budget is apportioned, with about half reserved for lodging.
    per_day = budget / days if days else 0
    allocation = [
        {"label": "Stay", "amount": round(per_day * 0.45, 2)},
        {"label": "Food", "amount": round(per_day * 0.25, 2)},
        {"label": "Activities", "amount": round(per_day * 0.20, 2)},
        {"label": "Local transport & buffer", "amount": round(per_day * 0.10, 2)},
    ]
    notes = ["Budget split is a planning guide for the whole group; it excludes long-distance travel to the destination.",
             "Check current opening hours, entry rules, transit routes, and seasonal conditions before booking."]
    if not matched:
        notes.insert(0, "Flexible destination template: venue names are not bundled for this city. Search locally for matching places in each suggested area.")
    return {
        "destination": destination, "days": days, "travelers": travelers, "budget": budget,
        "currency": currency, "per_person_day": per_person_day, "budget_level": level,
        "matched": bool(matched), "interests": interests, "pace": pace,
        "schedule": schedule, "allocation": allocation, "notes": notes,
    }
