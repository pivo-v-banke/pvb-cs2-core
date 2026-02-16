from fastapi import FastAPI

from controllers.demo import run_demo_parsing_controller
from controllers.match_source import match_source_list_controller, match_source_detail_controller, \
    match_source_create_controller, match_source_patch_controller, match_source_delete_controller, \
    collect_all_match_sources_controller, collect_match_source_controller
from controllers.ranking import recalibrate_all
from controllers.service import ping_controller
from controllers.webhook import webhook_list_controller, webhook_detail_controller, webhook_create_controller, \
    webhook_patch_controller, webhook_delete_controller, send_for_match


def prepare_routes(app: FastAPI) -> None:

    app.add_api_route("/api/ping/", ping_controller, methods=["GET"], tags=["Service"])
    app.add_api_route("/api/service/recalibrate_all/", recalibrate_all, methods=["POST"], tags=["Service"])

    app.add_api_route("/api/demo/parse/", run_demo_parsing_controller, methods=["POST"], tags=["Demo"])

    app.add_api_route("/api/webhook/", webhook_list_controller, methods=["GET"], tags=["Webhook"])
    app.add_api_route("/api/webhook/", webhook_create_controller, methods=["POST"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_detail_controller, methods=["GET"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_patch_controller, methods=["PATCH"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_delete_controller, methods=["DELETE"], tags=["Webhook"])

    app.add_api_route("/api/match_source/", match_source_list_controller, methods=["GET"], tags=["MatchSource"])
    app.add_api_route("/api/match_source/", match_source_create_controller, methods=["POST"], tags=["MatchSource"])
    app.add_api_route("/api/match_source/{match_source_id}/", match_source_detail_controller, methods=["GET"], tags=["MatchSource"])
    app.add_api_route("/api/match_source/{match_source_id}/", match_source_patch_controller, methods=["PATCH"], tags=["MatchSource"])
    app.add_api_route("/api/match_source/{match_source_id}/", match_source_delete_controller, methods=["DELETE"], tags=["MatchSource"])
    app.add_api_route("/api/match_source/collect_all/", collect_all_match_sources_controller, methods=["POST"], tags=["MatchSource"])
    app.add_api_route("/api/match_source/{match_source_id}/collect/", collect_match_source_controller, methods=["POST"], tags=["MatchSource"])

    app.add_api_route("/api/match/{match}/send_webhooks/", send_for_match, methods=["POST"], tags=["Match"])
