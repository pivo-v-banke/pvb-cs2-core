import logging

from components.parsing.parser import CS2DemoInfoParser
from components.steam_connector.models import CS2DemoInfo
from db import get_database
from db.managers.managers import MatchManager, PlayerManager, PlayerMatchStatManager
from db.models.models import Match

logger = logging.getLogger(__name__)

class DemoProcessing:
    def __init__(self, demo_file_path: str, demo_info: CS2DemoInfo) -> None:
        self.demo_file_path = demo_file_path
        self.parser = CS2DemoInfoParser(demo_file_path)
        self.demo_info = demo_info
        self.mongo_db = get_database()

    async def process_demo(self) -> tuple[Match, bool]:
        match, created = await self._create_match()
        await self._create_players(match)
        await self._create_match_stats(match)

        return match, created

    async def _create_match(self) -> tuple[Match, bool]:
        match_info = self.parser.get_match()
        match_id = self.demo_info.match_id
        match_manager = MatchManager(self.mongo_db)

        match, created = await match_manager.create_or_update(
            search_by={
                "cs2_match_id": match_id,
            },
            update={
                "match_code": self.demo_info.match_code,
                "player_steam_ids": match_info.player_steam_ids,
                "t_score": match_info.t_score,
                "ct_score": match_info.ct_score,
                "map_name": match_info.map_name,
            }
        )

        if created:
            logger.info("DemoParsing: created match %s", match_id)
        else:
            logger.info("DemoParsing: updated match %s", match_id)

        return match, created

    async def _create_players(self, match: Match) -> None:
        player_manager = PlayerManager(self.mongo_db)
        for player_steam_id in match.player_steam_ids:
            player_info = self.parser.get_player_info(player_steam_id)
            player, created = await player_manager.create_or_update(
                search_by={
                    "steam_id": player_info.steam_id,
                },
                update={
                    "display_name": player_info.display_name,
                }
            )
            if created:
                logger.info("DemoParsing: created player %s | %s", player_info.steam_id, player_info.display_name)
            else:
                logger.info("DemoParsing: updated player %s", player_info.steam_id)


    async def _create_match_stats(self, match: Match) -> None:
        match_stat_manager = PlayerMatchStatManager(self.mongo_db)
        match_id = match.cs2_match_id

        for player_stat_info in self.parser.get_stats():
            match_stat, created = await match_stat_manager.create_or_update(
                search_by={
                    "cs2_match_id": match_id,
                    "player_steam_id": player_stat_info.steam_id,
                },
                update={
                    "kills": player_stat_info.kills,
                    "deaths": player_stat_info.deaths,
                    "assists": player_stat_info.assists,
                }
            )
            if created:
                logger.info("DemoParsing: created match stat for player %s in match %s", player_stat_info.steam_id, match_id)
            else:
                logger.warning(
                    "DemoParsing: probably duplicated match: "
                    "updating existing match stat for player %s in match %s",
                    player_stat_info.steam_id,
                    match_id,
                )

