import pytest

from app import create_app, model, pipeline, simulate


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def test_clean_removes_nans_and_duplicates():
    raw = simulate.simulate_sensors(n_assets=2, hours=200)
    df = pipeline.clean(raw)
    assert not df[pipeline.SENSORS].isna().any().any()
    assert not df.duplicated(["timestamp", "asset_id"]).any()
    assert df["temperature"].abs().max() < 150  # spikes removed


def test_model_beats_chance():
    feat = pipeline.add_features(pipeline.clean(simulate.simulate_sensors()))
    _, _, metrics = model.train(feat)
    assert metrics["roc_auc"] > 0.8


def test_endpoints(client):
    assert client.get("/api/health").json == {"status": "ok"}
    assets = client.get("/api/assets").json
    assert len(assets) == 8
    aid = assets[0]["asset_id"]
    assert "risk" in client.get(f"/api/timeseries/{aid}").json
    assert client.get("/api/timeseries/nope").status_code == 404
    assert isinstance(client.get("/api/alerts").json, list)
    assert "by_type" in client.get("/api/maintenance").json
    assert client.get("/").status_code == 200
