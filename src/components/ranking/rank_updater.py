import asyncio
import logging

from conf.ranking import RANKING_INITIAL_RANK, RANKING_MIN_RANK, RANKING_MAX_RANK
from db import get_database
from db.managers.managers import MatchManager, PlayerMatchStatManager, PlayerManager, PlayerRankChangeManager
from db.models.models import Match, Player, PlayerMatchStat
from utils.math_utils import clamp

logger = logging.getLogger(__name__)


class PlayerRankCalculator:

    @classmethod
    def calculate_player_rank_change(cls, player: Player, match_stat: PlayerMatchStat) -> tuple[int, int]:
        current_rank = player.rank or RANKING_INITIAL_RANK

        kd_diff = match_stat.kills - match_stat.deaths
        if kd_diff > 1:
            new_rank = current_rank + 1
        elif kd_diff < -1:
            new_rank = current_rank - 1
        else:
            new_rank = current_rank

        return current_rank, clamp(new_rank, RANKING_MIN_RANK, RANKING_MAX_RANK)


class RankUpdater:

    def __init__(self, cs2_match_id: int) -> None:
        self.cs2_match_id = cs2_match_id
        self.db = get_database()
        self.match_manager = MatchManager(self.db)
        self.player_manager = PlayerManager(self.db)
        self.player_stat_manager = PlayerMatchStatManager(self.db)
        self.rank_change_manager = PlayerRankChangeManager(self.db)


    async def update_player_ranks(self, overwrite: bool = False) -> None:
        logger.info("RankUpdater: Calculating ranks by match %s", self.cs2_match_id)

        match = await self._get_match()
        update_tasks = []
        for player_steam_id in match.player_steam_ids:
            update_tasks.append(
                self._update_player_rank(player_steam_id, overwrite)
            )

        await asyncio.gather(*update_tasks)


    async def _get_match(self) -> Match:
        match = await self.match_manager.get(raise_not_found=True, cs2_match_id=self.cs2_match_id)

        return match

    async def _update_player_rank(self, player_steam_id: str, overwrite: bool) -> None:
        player: Player | None = await self.player_manager.get(steam_id=player_steam_id)
        if not player:
            logger.error("RankUpdater: Player with steam id %s not exists in DB", player_steam_id)
            return

        player_stat: PlayerMatchStat = await self.player_stat_manager.get(
            cs2_match_id=self.cs2_match_id,
            player_steam_id=player_steam_id,
        )
        if not player_stat:
            logger.error(
                "RankUpdater: Could not find match statistic for match = %s | player_steam_id = %s",
                self.cs2_match_id,
                player_steam_id,
            )
            return

        existing_rank_change = await self.rank_change_manager.get(
            cs2_match_id=self.cs2_match_id,
            player_steam_id=player_steam_id,
        )
        if existing_rank_change and not overwrite:
            logger.warning(
                "RankUpdater: Rank for player %s and match %s was already calculated. Skipping",
                player_steam_id,
                self.cs2_match_id,
            )
            return

        elif existing_rank_change:
            logger.warning(
                "RankUpdater: Rank for player %s and match %s was already calculated. Overwriting",
                player_steam_id,
                self.cs2_match_id,
            )

        old_rank, new_rank = PlayerRankCalculator.calculate_player_rank_change(
            player=player,
            match_stat=player_stat,
        )
        logger.info("RankUpdater: Setting new rank for player %s to %s", player_steam_id, new_rank)

        await self.player_manager.update(
            id_=player.id,
            patch={
                "rank": new_rank,
            }
        )
        await self.rank_change_manager.create_or_update(
            search_by={
                "player_steam_id": player_steam_id,
                "cs2_match_id": self.cs2_match_id,
            },
            update={
                "old_rank": old_rank,
                "new_rank": new_rank,
            }
        )


