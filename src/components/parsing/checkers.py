from components.parsing.models import DemoParsingState
from db import get_mongo_db
from db.managers.managers import DemoParsingTaskManager

class DemoParsingDeduplicationError(ValueError):
    pass

class DemoParsingDeduplicationChecker:

    @classmethod
    async def check_parsing_duplicate(cls, match_code: str, raise_exc: bool = False) -> bool:
        parsing_task_manager = DemoParsingTaskManager(get_mongo_db())

        existing_parsing_tasks = await parsing_task_manager.list_(
            filter_by={
                "state": {
                    "$in": [
                        DemoParsingState.SUCCESS,
                        DemoParsingState.IN_PROGRESS,
                    ]
                }
            }
        )
        if existing_parsing_tasks:
            duplicated = True
        else:
            duplicated = False

        if duplicated and raise_exc:
            raise DemoParsingDeduplicationError(f"{match_code} Already Parsed")

        return duplicated
