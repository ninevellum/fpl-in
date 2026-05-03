"""Fantasy Premier League data tools."""
import httpx



def get_league_managers(league_id):
    """Fetch managers in a classic mini-league. Returns list of (manager_id, team_name, player_name) tuples."""
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    data = httpx.get(url).json()
    results = data["standings"]["results"]
    return [(m["entry"], m["entry_name"], m["player_name"]) for m in results]

def top_players(n=10):
    url = f"https://fantasy.premierleague.com/api/bootstrap-static/""
    data = httpx.get(url).json()
    players = sorted(data["elements"], key=lambda p: p["total_points"], reverse=True)
    return [(p["web_name"], p["total_points"]) for p in players[:n]]

if __name__ == "__main__":
    managers = get_league_managers(314)
    print(f"Found {len(managers)} managers")
    for manager_id, team_name, player_name in managers[:5]:
        print(f"  {manager_id}  {team_name}  ({player_name})")