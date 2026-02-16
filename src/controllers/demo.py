from api_models.demo import RunDemoParsingRequest
from components.runner.parsing_runner import run_demo_parsing


async def run_demo_parsing_controller(request: RunDemoParsingRequest) -> None:

    match_code = request.match_code
    await run_demo_parsing(match_code)

    return None
