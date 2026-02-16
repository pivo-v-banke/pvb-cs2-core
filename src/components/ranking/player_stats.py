import asyncio

from db import get_mongo_db
from db.managers.managers import PlayerManager, PlayerMatchStatManager
from db.models.models import Player, PlayerMatchStat


class PlayerStatsUpdater:


    def __init__(self):
        self.db = get_mongo_db()
        self.player_manager = PlayerManager(self.db)
        self.player_stats_manager = PlayerMatchStatManager(self.db)


    async def calculate_players_stats(self, player_steam_ids: list[str]):
        tasks = []
        for player_steam_id in player_steam_ids:
            tasks.append(self._calculate_for_player(player_steam_id))

        await asyncio.gather(*tasks)


    async def _calculate_for_player(self, player_steam_id: str):
        match_stats: list[PlayerMatchStat] = await self.player_stats_manager.list_(
            filter_by={
                "player_steam_id": player_steam_id,
            }
        )
        kills_total = 0
        deaths_total = 0
        games_played = 0
        plus_kd_games = 0
        minus_kd_games = 0

        for match_stat in match_stats:
            kills_total += match_stat.kills
            deaths_total += match_stat.deaths
            if match_stat.kills >= match_stat.deaths:
                plus_kd_games += 1
            else:
                minus_kd_games += 1
            games_played += 1

        avg_kd = kills_total / deaths_total if deaths_total else 0

        await self.player_manager.update(
            search_by={
                "steam_id": player_steam_id,
            },
            patch={
                "avg_kd": avg_kd,
                "plus_kd_games": plus_kd_games,
                "minus_kd_games": minus_kd_games,
                "games_played": games_played,
            }
        )


