from db.models.models import Match
from tasks.demo import all_players_calibration_task


async def recalibrate_all():


    all_players_calibration_task.apply_async()
