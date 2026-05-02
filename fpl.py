"""Top 10 FPL players by total points."""
import httpx

URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

def top_players(n=10):
    data = httpx.get(URL).json()
    players = sorted(data["elements"], key=lambda p: p["total_points"], reverse=True)
    return [(p["web_name"], p["total_points"]) for p in players[:n]]

if __name__ == "__main__":
    for name, points in top_players():
        print(f"{points:>4}  {name}")
