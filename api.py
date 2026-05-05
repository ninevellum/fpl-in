"""FastAPI web service for FPL insights."""
from fastapi import FastAPI

from fpl import (
    current_gameweek,
    get_player_lookup,
    get_league_managers,
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