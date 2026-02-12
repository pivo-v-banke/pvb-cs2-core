from fastapi import FastAPI

from controllers.demo import run_demo_parsing_controller
from controllers.service import ping_controller
from controllers.webhook import webhook_list_controller, webhook_detail_controller, webhook_create_controller, \
    webhook_patch_controller, webhook_delete_controller


def prepare_routes(app: FastAPI) -> None:

    app.add_api_route("/api/ping/", ping_controller, methods=["GET"], tags=["Service"])
    app.add_api_route("/api/demo/parse/", run_demo_parsing_controller, methods=["POST"], tags=["Demo"])

    app.add_api_route("/api/webhook/", webhook_list_controller, methods=["GET"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_detail_controller, methods=["GET"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_create_controller, methods=["POST"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_patch_controller, methods=["PATCH"], tags=["Webhook"])
    app.add_api_route("/api/webhook/{webhook_id}/", webhook_delete_controller, methods=["DELETE"], tags=["Webhook"])
