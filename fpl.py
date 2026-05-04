"""Fantasy Premier League data tools."""
import httpx

def get_player_lookup():
    """Return a dict mapping player_id -> web_name for all FPL players."""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    data = httpx.get(url).json()
    return {p["id"]: p["web_name"] for p in data["elements"]}

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

def league_ownership(league_id, gameweek):
    """For each player, count how many managers in the league own them.
    Returns dict mapping player_id -> count."""
    managers = get_league_managers(league_id)
    counts = {}
    for manager_id, _, _ in managers:
        picks = get_manager_picks(manager_id, gameweek)
        for player_id in picks:
            counts[player_id] = counts.get(player_id, 0) + 1
    return counts

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
    players = get_player_lookup()

    league_id = 314
    counts = league_ownership(league_id, gw)
    total_managers = len(get_league_managers(league_id))

    differentials = []
    template = []
    for player_id, count in counts.items():
        ownership_pct = count / total_managers * 100
        if 5 <= ownership_pct < 25:
            differentials.append((players[player_id], count, ownership_pct))
        elif ownership_pct >= 70:
            template.append((players[player_id], count, ownership_pct))

    differentials.sort(key=lambda x: x[1], reverse=True)
    template.sort(key=lambda x: x[1], reverse=True)

    print(f"Gameweek {gw} — League {league_id} ({total_managers} managers)\n")

    print(f"Template players (≥70% owned):")
    for name, count, pct in template:
        print(f"  {count:>3}/{total_managers}  {pct:>5.1f}%  {name}")

    print(f"\nDifferentials (5-25% owned):")
    for name, count, pct in differentials:
        print(f"  {count:>3}/{total_managers}  {pct:>5.1f}%  {name}")