"""FastAPI web service for FPL insights."""
from fastapi import FastAPI

from fpl import (
    current_gameweek,
    get_player_lookup,
    league_ownership,
    top_players,
)

app = FastAPI(title="FPL Insights", description="Fantasy Premier League data tools")


@app.get("/")
def root():
    return {"message": "FPL Insights API. See /docs for available endpoints."}


@app.get("/gameweek")
def gameweek():
    return {"gameweek": current_gameweek()}


@app.get("/top-players")
def top():
    players = top_players(10)
    return [{"name": name, "points": points} for name, points in players]


@app.get("/league/{league_id}/differentials")
def differentials(league_id: int):
    gw = current_gameweek()
    players = get_player_lookup()
    counts, total_managers = league_ownership(league_id, gw)
    differentials = []
    template = []
    for player_id, count in counts.items():
        ownership_pct = count / total_managers * 100
        entry = {
            "name": players[player_id],
            "count": count,
            "total": total_managers,
            "ownership_pct": round(ownership_pct, 1),
        }
        if 5 <= ownership_pct < 25:
            differentials.append(entry)
        elif ownership_pct >= 70:
            template.append(entry)

    differentials.sort(key=lambda x: x["count"], reverse=True)
    template.sort(key=lambda x: x["count"], reverse=True)

    return {
        "league_id": league_id,
        "gameweek": gw,
        "total_managers": total_managers,
        "template": template,
        "differentials": differentials,
    }