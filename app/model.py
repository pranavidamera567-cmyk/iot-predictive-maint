"""Baseline failure-risk model."""
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, roc_auc_score

from .pipeline import feature_columns


def train(feat):
    """Time-ordered split (last 25% held out) to avoid leakage."""
    cols = feature_columns(feat)
    cutoff = feat["timestamp"].quantile(0.75)
    tr, te = feat[feat["timestamp"] <= cutoff], feat[feat["timestamp"] > cutoff]
    clf = RandomForestClassifier(n_estimators=150, class_weight="balanced", random_state=0, n_jobs=-1)
    clf.fit(tr[cols], tr["fail_within_24h"])
    proba = clf.predict_proba(te[cols])[:, 1]
    pred = proba >= 0.5
    y = te["fail_within_24h"]
    metrics = {
        "roc_auc": float(roc_auc_score(y, proba)) if y.nunique() > 1 else None,
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "train_rows": len(tr), "test_rows": len(te),
    }
    return clf, cols, metrics


def score(clf, cols, feat):
    out = feat[["timestamp", "asset_id"]].copy()
    out["risk"] = clf.predict_proba(feat[cols])[:, 1]
    return out
