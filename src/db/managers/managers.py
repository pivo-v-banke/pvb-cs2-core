from db.managers.base import BaseMongoDBManager
from db.models.models import DemoParsingTask, Match, Player, PlayerMatchStat, PlayerRankChange, MatchStatsWebhook, \
    MatchSource


class DemoParsingTaskManager(BaseMongoDBManager):
    model = DemoParsingTask
    collection_name = 'demo_parsing_tasks'


class MatchManager(BaseMongoDBManager):
    model = Match
    collection_name = 'matches'


class PlayerManager(BaseMongoDBManager):
    model = Player
    collection_name = 'players'

class MatchSourceManager(BaseMongoDBManager):
    model = MatchSource
    collection_name = 'match_sources'

class PlayerMatchStatManager(BaseMongoDBManager):
    model = PlayerMatchStat
    collection_name = 'player_match_stats'


class PlayerRankChangeManager(BaseMongoDBManager):
    model = PlayerRankChange
    collection_name = 'player_rank_changes'

class MatchStatsWebhookManager(BaseMongoDBManager):
    model = MatchStatsWebhook
    collection_name = 'webhooks'