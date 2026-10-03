import pandas as pd

from services import new_system_service as intake
from services.dataset_service import parse_system_dataset_filename


def test_csv_intake_city_and_duplicate_names_remain_available(tmp_path, monkeypatch):
    times = pd.date_range("2026-06-01 08:00", periods=60, freq="5min")
    source = tmp_path / "pv.csv"
    pd.DataFrame({"timestamp": times, "power_w": 2000}).to_csv(source, index=False)
    def weather(**kwargs):
        return pd.DataFrame({"time": times, "ghi_pyr": 500, "dni": 400, "dhi": 100,
                             "air_temperature": 30, "relative_humidity": 50, "wind_speed": 2})
    monkeypatch.setattr(intake, "_fetch_openmeteo_weather", weather)
    monkeypatch.setattr(intake, "PV_DATA_DIR", tmp_path / "data")
    request = dict(system_id=99, capacity_kw=4.0, city="New York/../../test", lat=31.0, lon=74.0,
                   uploaded_file_path=source)
    first = intake.create_new_system_dataset(**request)
    second = intake.create_new_system_dataset(**request)
    assert first["row_count"] == 60
    assert first["file_name"] != second["file_name"]
    for result in (first, second):
        from pathlib import Path
        path = Path(result["output_path"])
        assert path.parent == tmp_path / "data" and path.is_file()
        assert parse_system_dataset_filename(path)["system_id"] == 99
