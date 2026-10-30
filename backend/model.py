"""XGBoost demand forecasting with recursive multi-day prediction and what-if scenarios."""
import numpy as np, pandas as pd
from xgboost import XGBRegressor
import data

FEATS = ["pid", "dow", "month", "price", "promo", "lag1", "lag7", "roll7"]
state = {"model": None, "metrics": {}}

def _features(df):
    df = df.sort_values(["product_id", "date"]).copy()
    g = df.groupby("product_id")["units"]
    df["lag1"], df["lag7"] = g.shift(1), g.shift(7)
    df["roll7"] = g.transform(lambda s: s.shift(1).rolling(7).mean())
    df["pid"], df["dow"], df["month"] = df["product_id"], df["date"].dt.dayofweek, df["date"].dt.month
    df["price"] = df["product_id"].map(data.products().set_index("id")["price"])
    return df.dropna()

def train():
    df = _features(data.sales())
    cut = df["date"].max() - pd.Timedelta(days=28)
    tr, te = df[df["date"] <= cut], df[df["date"] > cut]
    m = XGBRegressor(n_estimators=250, max_depth=4, learning_rate=0.07, subsample=0.9, random_state=0)
    m.fit(tr[FEATS], tr["units"])
    p = m.predict(te[FEATS])
    err = te["units"].values - p
    base = te["units"].values - te["roll7"].values
    state["model"] = m
    state["metrics"] = {
        "mae": round(float(np.abs(err).mean()), 2), "rmse": round(float(np.sqrt((err ** 2).mean())), 2),
        "baseline_mae": round(float(np.abs(base).mean()), 2),
        "improvement_pct": round(float((1 - np.abs(err).mean() / np.abs(base).mean()) * 100), 1),
        "train_rows": int(len(tr)), "test_rows": int(len(te)),
    }

def forecast(days=7, promo_category=None, footfall_pct=0):
    """Return {product_id: [predicted units per day]} for the next `days` days."""
    prods, sales = data.products(), data.sales()
    hist = {pid: list(g.sort_values("date")["units"].astype(float)[-14:]) for pid, g in sales.groupby("product_id")}
    last = sales["date"].max()
    out = {pid: [] for pid in prods["id"]}
    promo_ids = set(prods[prods["category"] == promo_category]["id"]) if promo_category else set()
    for k in range(1, days + 1):
        d = last + pd.Timedelta(days=k)
        X = pd.DataFrame([{"pid": r.id, "dow": d.dayofweek, "month": d.month, "price": r.price,
                           "promo": int(r.id in promo_ids), "lag1": hist[r.id][-1], "lag7": hist[r.id][-7],
                           "roll7": np.mean(hist[r.id][-7:])} for r in prods.itertuples()])[FEATS]
        pred = np.clip(state["model"].predict(X), 0, None) * (1 + footfall_pct / 100)
        for r, v in zip(prods.itertuples(), pred):
            out[r.id].append(float(v)); hist[r.id].append(float(v))
    return out
