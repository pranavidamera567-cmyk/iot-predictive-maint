from flask import Flask, jsonify, render_template, request

from . import model, pipeline, simulate, store

RISK_ALERT = 0.7


def build_state():
    raw = simulate.simulate_sensors()
    feat = pipeline.add_features(pipeline.clean(raw))
    clf, cols, metrics = model.train(feat)
    scored = feat.merge(model.score(clf, cols, feat), on=["timestamp", "asset_id"])
    maint = simulate.simulate_maintenance()
    store.save(store.get_engine(), sensor_readings=scored, maintenance_history=maint)
    return {"data": scored, "maint": maint, "metrics": metrics}


def create_app(state=None):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    S = state or build_state()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/metrics")
    def metrics():
        return jsonify(S["metrics"])

    @app.get("/api/assets")
    def assets():
        latest = S["data"].sort_values("timestamp").groupby("asset_id").tail(1)
        recent = S["data"].sort_values("timestamp").groupby("asset_id").tail(6).groupby("asset_id")["risk"].max()
        rows = [{"asset_id": r.asset_id, "temperature": round(r.temperature, 1),
                 "vibration": round(r.vibration, 2), "pressure": round(r.pressure, 1),
                 "risk": round(float(recent[r.asset_id]), 3),
                 "status": "alert" if recent[r.asset_id] >= RISK_ALERT else "ok"}
                for r in latest.itertuples()]
        return jsonify(sorted(rows, key=lambda r: -r["risk"]))

    @app.get("/api/timeseries/<asset_id>")
    def timeseries(asset_id):
        hours = request.args.get("hours", 168, type=int)
        d = S["data"][S["data"]["asset_id"] == asset_id].tail(hours)
        if d.empty:
            return jsonify(error="unknown asset"), 404
        return jsonify({"timestamp": d["timestamp"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
                        **{c: d[c].round(2).tolist() for c in ["temperature", "vibration", "risk"]}})

    @app.get("/api/alerts")
    def alerts():
        d = S["data"]
        hot = d[d["risk"] >= RISK_ALERT].sort_values("timestamp")
        first = hot.groupby("asset_id").tail(1).sort_values("risk", ascending=False)
        return jsonify([{"asset_id": r.asset_id, "timestamp": str(r.timestamp), "risk": round(float(r.risk), 3)}
                        for r in first.itertuples()])

    @app.get("/api/maintenance")
    def maintenance():
        m = S["maint"].copy()
        m["month"] = m["date"].dt.strftime("%Y-%m")
        by_type = m.groupby("type").agg(events=("type", "size"), cost=("cost", "sum")).round(2)
        by_month = m.groupby("month").agg(events=("type", "size"), downtime=("downtime_hours", "sum")).round(1)
        return jsonify(by_type=by_type.reset_index().to_dict("records"),
                       by_month=by_month.reset_index().to_dict("records"))

    return app
