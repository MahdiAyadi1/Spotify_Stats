"""Azure Functions entry point.

Only this module knows about Azure Functions. The work is done by
`spotify_stats.service`; nothing is stored or logged from the upload.
"""

import json

import azure.functions as func

from spotify_stats.service import build_stats_result

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="stats", methods=["POST"])
def stats(req: func.HttpRequest) -> func.HttpResponse:
    result = build_stats_result(req.get_body())
    return func.HttpResponse(
        json.dumps(result.body),
        status_code=result.status,
        mimetype="application/json",
    )


@app.route(route="upload-check", methods=["POST"])
def upload_check(req: func.HttpRequest) -> func.HttpResponse:
    """TEMPORARY: reports the size of the uploaded ZIP, to test upload limits on Azure.

    Remove once the upload of a real export is confirmed to work on Azure.
    """
    return func.HttpResponse(
        json.dumps({"received_zip_bytes": len(req.get_body())}),
        mimetype="application/json",
    )
