import base64
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from flask import Flask
from werkzeug.security import generate_password_hash

import wsgi
from services import forecasting_service as pv
from services.access_service import configure_access
from services.config_service import CONFIG_DIR
from services.runtime_service import MODEL_RUN_LOCK, initialize_runtime, safe_child
from services.upload_service import decode_csv_upload, save_csv_upload


@pytest.mark.parametrize("path", ["/", "/healthz", "/_dash-layout", "/_dash-dependencies", "/assets/style.css", "/assets/s2cool_logo.png"])
def test_http_routes(path):
    assert wsgi.server.test_client().get(path).status_code == 200


@pytest.mark.parametrize("tab", ["dashboard", "data-analysis", "pv-forecasting", "cooling-demand"])
def test_working_tabs(tab):
    response = wsgi.server.test_client().post("/_dash-update-component", json={
        "output": "page-content.children",
        "outputs": {"id": "page-content", "property": "children"},
        "changedPropIds": ["app-tabs.value"],
        "inputs": [{"id": "app-tabs", "property": "value", "value": tab},
                   {"id": "system-select", "property": "value", "value": 6}],
        "state": [],
    })
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.json["response"]["page-content"]["children"]


def test_saved_model_upload_cannot_deserialize(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Untrusted model upload reached joblib.load")
    monkeypatch.setattr(pv.joblib, "load", forbidden)
    with pytest.raises(pv.ForecastingError, match="uploads are disabled"):
        pv.load_trained_model(b"untrusted pickle payload")
    dependencies = wsgi.server.test_client().get("/_dash-dependencies").get_data(as_text=True)
    assert "pv-trained-model-upload" not in dependencies


@pytest.mark.parametrize("name", ["../../outside.csv", "..\\..\\outside.csv", "/outside.csv", "C:\\outside.csv"])
def test_upload_uses_server_filename(tmp_path, name):
    data = "data:text/csv;base64," + base64.b64encode(b"a,b\n1,2\n").decode()
    path = save_csv_upload(data, name, tmp_path / "uploads")
    assert path.parent == tmp_path / "uploads"
    assert path.name != name and path.read_bytes() == b"a,b\n1,2\n"
    assert not (tmp_path / "outside.csv").exists()


def test_upload_limits_and_invalid_base64(monkeypatch):
    import services.upload_service as uploads
    monkeypatch.setattr(uploads, "MAX_UPLOAD_BYTES", 4)
    with pytest.raises(ValueError, match="too large|up to"):
        decode_csv_upload("data:text/csv;base64," + base64.b64encode(b"12345").decode(), "x.csv")
    with pytest.raises(ValueError):
        decode_csv_upload("data:text/csv;base64,!?!!", "x.csv")
    with pytest.raises(ValueError, match="CSV"):
        decode_csv_upload("data:text/plain;base64,YQ==", "model.joblib")


def test_dataset_path_traversal_rejected(tmp_path):
    for name in ("../outside.csv", "..\\outside.csv", "/outside.csv"):
        with pytest.raises(ValueError):
            safe_child(tmp_path, name)


def test_demo_login_covers_dash_callbacks(monkeypatch):
    monkeypatch.setenv("S2COOL_AUTH_USER", "demo")
    monkeypatch.setenv("S2COOL_PASSWORD_HASH", generate_password_hash("test-demo-password"))
    server = Flask("auth-test")
    configure_access(server)
    server.add_url_rule("/_dash-update-component", view_func=lambda: "ok", methods=["POST"])
    client = server.test_client()
    assert client.post("/_dash-update-component").status_code == 401
    assert client.post("/_dash-update-component", auth=("demo", "wrong")).status_code == 401
    assert client.post("/_dash-update-component", auth=("d\u00e9mo", "wrong")).status_code == 401
    assert client.post("/_dash-update-component", auth=("demo", "test-demo-password")).status_code == 200
    assert client.get("/healthz").json == {"status": "ok"}


def test_hosted_login_configuration_is_required(monkeypatch):
    monkeypatch.setenv("S2COOL_REQUIRE_AUTH", "1")
    with pytest.raises(RuntimeError, match="Set both"):
        configure_access(Flask("missing-login"))


def test_second_model_run_is_rejected_while_pages_stay_available():
    with MODEL_RUN_LOCK:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(pv.train_model, {})
            with pytest.raises(pv.ForecastingError, match="Another model run"):
                future.result()
        assert wsgi.server.test_client().get("/healthz").status_code == 200


def test_seed_does_not_replace_saved_profiles():
    path = CONFIG_DIR / "cooling_sites.json"
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(json.dumps({"sites": [], "saved": True}), encoding="utf-8")
        initialize_runtime()
        assert json.loads(path.read_text(encoding="utf-8"))["saved"]
    finally:
        path.write_text(original, encoding="utf-8")
