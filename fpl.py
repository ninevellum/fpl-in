"""Fantasy Premier League data tools."""
import httpx

def current_gameweek():
    """Return the current gameweek number from FPL's bootstrap data."""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    data = httpx.get(url).json()
    for event in data["events"]:
        if event["is_current"]:
            return event["id"]
    return None

def get_manager_picks(manager_id, gameweek):
    """Return list of player IDs in this manager's squad for the given gameweek."""
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gameweek}/picks/"
    data = httpx.get(url).json()
    return [pick["element"] for pick in data["picks"]]

def get_league_managers(league_id):
    """Fetch managers in a classic mini-league. Returns list of (manager_id, team_name, player_name) tuples."""
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    data = httpx.get(url).json()
    results = data["standings"]["results"]
    return [(m["entry"], m["entry_name"], m["player_name"]) for m in results]

def top_players(n=10):
    url = f"https://fantasy.premierleague.com/api/bootstrap-static/"
    data = httpx.get(url).json()
    players = sorted(data["elements"], key=lambda p: p["total_points"], reverse=True)
    return [(p["web_name"], p["total_points"]) for p in players[:n]]

if __name__ == "__main__":
    gw = current_gameweek()
    print(f"Current gameweek: {gw}")

    managers = get_league_managers(314)
    first_manager_id, team_name, player_name = managers[0]
    picks = get_manager_picks(first_manager_id, gw)
    print(f"{team_name} ({player_name}) has {len(picks)} players: {picks}")