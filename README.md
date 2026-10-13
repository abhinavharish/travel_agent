# Wayfarer — Smart Travel Agent

A small, local Python web app that builds a day-by-day travel itinerary from your destination, dates, trip length, group size, budget, pace, and interests.

## Run it

1. Install Python 3.9 or newer if it is not already installed.
2. Open a terminal in this folder.
3. Run `python app.py` (on Windows, `py app.py` also works).
4. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
5. Press **Ctrl+C** in the terminal to stop the app.

It uses only Python's standard library. There are no accounts, API keys, or dependency installs.

## What it does

- Creates a 1–14 day plan and adapts the number of activities to your chosen pace.
- Prioritizes activities that match your interests and favors lower-cost suggestions for tighter budgets.
- Includes estimated entry costs for some highlights and a per-day budget guide for the group.
- Includes bundled highlight ideas for Paris, London, Tokyo, Rome, New York, and Delhi. Other destinations get a flexible neighborhood and activity template; it avoids making up specific venue names.
- Lets you add more cities and highlights by editing `destinations.json`. Each place has a name, area, short description, interest tags, estimated visit duration, and approximate entry cost.

## Planning notes

This is an offline planning helper, not a live booking or search service. Place lists and cost estimates are illustrative and may be stale or incomplete. The budget guide is a rough split of the total trip budget across lodging, food, activities, and local transport; it excludes getting to the destination. Confirm current opening hours, access, ticket prices, transit, and travel requirements before making reservations.
