"""Azure Functions entry point.

Only this module knows about Azure Functions. The statistics logic lives in
the `spotify_stats` package and must stay free of Azure imports.
"""

import json

import azure.functions as func

from spotify_stats.service import build_stats_result

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="stats", methods=["POST"])
def stats(req: func.HttpRequest) -> func.HttpResponse:
    """Compute the listening statistics for a Spotify export ZIP."""
    result = build_stats_result(req.get_body())
    return func.HttpResponse(
        json.dumps(result.body),
        mimetype="application/json",
        status_code=result.status,
    )


@app.route(route="upload_check", methods=["POST"])
def upload_check(req: func.HttpRequest) -> func.HttpResponse:
    """Temporary helper for checking upload size on Azure."""
    export_zip = req.get_body()
    return func.HttpResponse(
        json.dumps({"received_zip_bytes": len(export_zip)}),
        mimetype="application/json",
    )
