import json

import azure.functions as func

from function_app import app
from tests.export_builders import make_export_zip, track_play

# app.get_functions() can only be called once: a second call reports duplicate names.
REGISTERED_FUNCTIONS = {function.get_function_name(): function for function in app.get_functions()}


def call(function_name: str, body: bytes, params: dict | None = None) -> func.HttpResponse:
    """Call a registered function the way the Azure runtime would."""
    function = REGISTERED_FUNCTIONS[function_name]
    request = func.HttpRequest(
        method="POST", url=f"/api/{function_name}", body=body, headers={}, params=params or {}
    )
    return function.get_user_function()(request)


def test_stats_returns_json_statistics_for_a_valid_export():
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [track_play()]})

    response = call("stats", export_zip.getvalue())

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert json.loads(response.get_body())["summary"]["total_plays"] == 1


def test_stats_returns_a_json_error_for_an_invalid_upload():
    response = call("stats", b"not a zip")

    assert response.status_code == 400
    assert "error" in json.loads(response.get_body())


def test_upload_check_reports_the_number_of_bytes_received():
    response = call("upload_check", b"12345")

    assert json.loads(response.get_body()) == {"received_zip_bytes": 5}


def test_stats_passes_the_query_parameters_to_the_service():
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [track_play()]})

    response = call("stats", export_zip.getvalue(), params={"timezone": "Mars/Base"})

    assert response.status_code == 400
    assert "timezone" in json.loads(response.get_body())["error"].lower()
