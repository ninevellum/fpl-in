"""Fantasy Premier League data tools."""
import asyncio
import time
import httpx


# --- Caching ---
# Simple TTL cache: maps a key to (value, expires_at_timestamp).
# Separate dict per data source so TTLs and key shapes stay independent.

_TTL_SECONDS = 300  # 5 minutes — sensible default for FPL data

_bootstrap_cache = {}       # key: "_" (single entry, no real key)
_league_managers_cache = {} # key: league_id
_manager_picks_cache = {}   # key: (manager_id, gameweek)


def _cache_get(cache, key):
    """Return cached value for key if present and unexpired, else None."""
    entry = cache.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        return None
    return value


def _cache_set(cache, key, value):
    """Store value in cache with expiry _TTL_SECONDS from now."""
    cache[key] = (value, time.time() + _TTL_SECONDS)


# --- FPL data fetchers ---

def _bootstrap():
    """Fetch and cache the FPL bootstrap-static blob."""
    cached = _cache_get(_bootstrap_cache, "_")
    if cached is not None:
        return cached
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    data = httpx.get(url).json()
    _cache_set(_bootstrap_cache, "_", data)
    return data


def get_player_lookup():
    """Return a dict mapping player_id -> web_name for all FPL players."""
    data = _bootstrap()
    return {p["id"]: p["web_name"] for p in data["elements"]}


async def get_league_managers(league_id):
    """Fetch a classic mini-league. Returns (league_name, managers) where
    managers is a list of (manager_id, team_name, player_name) tuples."""
    cached = _cache_get(_league_managers_cache, league_id)
    if cached is not None:
        return cached
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    league_name = data["league"]["name"]
    results = data["standings"]["results"]
    managers = [(m["entry"], m["entry_name"], m["player_name"]) for m in results]
    payload = (league_name, managers)
    _cache_set(_league_managers_cache, league_id, payload)
    return payload


async def get_manager_picks(client, manager_id, gameweek):
    """Return list of player IDs in this manager's squad for the given gameweek."""
    key = (manager_id, gameweek)
    cached = _cache_get(_manager_picks_cache, key)
    if cached is not None:
        return cached
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gameweek}/picks/"
    response = await client.get(url)
    data = response.json()
    picks = [pick["element"] for pick in data["picks"]]
    _cache_set(_manager_picks_cache, key, picks)
    return picks


def current_gameweek():
    """Return the current gameweek number from FPL's bootstrap data."""
    data = _bootstrap()
    for event in data["events"]:
        if event["is_current"]:
            return event["id"]
    return None


async def league_ownership(league_id, gameweek):
    """For each player, count how many managers in the league own them.
    Returns (league_name, counts, total_managers) where counts maps player_id -> count."""
    league_name, managers = await get_league_managers(league_id)
    async with httpx.AsyncClient() as client:
        all_picks = await asyncio.gather(
            *(get_manager_picks(client, manager_id, gameweek) for manager_id, _, _ in managers)
        )
    counts = {}
    for picks in all_picks:
        for player_id in picks:
            counts[player_id] = counts.get(player_id, 0) + 1
    return league_name, counts, len(managers)

def top_players(n=10):
    """Return top n FPL players by total points."""
    data = _bootstrap()
    players = sorted(data["elements"], key=lambda p: p["total_points"], reverse=True)
    return [(p["web_name"], p["total_points"]) for p in players[:n]]


async def _main():
    gw = current_gameweek()
    players = get_player_lookup()

    league_id = 314
    league_name, counts, total_managers = await league_ownership(league_id, gw)

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

    print(f"Gameweek {gw} — {league_name} ({total_managers} managers)")
    
    print("\nTemplate players (≥70% owned):")
    for name, count, pct in template:
        print(f"  {count:>3}/{total_managers}  {pct:>5.1f}%  {name}")

    print("\nDifferentials (5-25% owned):")
    for name, count, pct in differentials:
        print(f"  {count:>3}/{total_managers}  {pct:>5.1f}%  {name}")


if __name__ == "__main__":
    asyncio.run(_main())