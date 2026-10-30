"""RetailTwin AI backend (FastAPI)."""
import math
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import data, model

app = FastAPI(title="RetailTwin AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    data.init_db()
    model.train()

def status(cover):
    return "Stockout risk" if cover < 3 else "Overstock" if cover > 21 else "Healthy"

def table(days=7, promo=None, footfall=0):
    prods, fc = data.products(), model.forecast(days, promo, footfall)
    rows = []
    for r in prods.itertuples():
        avg = sum(fc[r.id]) / days
        cover = r.stock / avg if avg else 99
        need = max(0, math.ceil(14 * avg - r.stock))
        rows.append(dict(id=int(r.id), name=r.name, category=r.category, price=float(r.price), stock=int(r.stock),
                         forecast_units=round(sum(fc[r.id])), avg_daily=round(avg, 1), days_cover=round(cover, 1),
                         status=status(cover), reorder_qty=need, forecast_revenue=round(sum(fc[r.id]) * r.price),
                         lost_sales=round(max(0, sum(fc[r.id]) - r.stock) * r.price)))
    return rows

@app.get("/api/health")
def health(): return {"ok": True}

@app.get("/api/model/metrics")
def metrics(): return model.state["metrics"]

@app.get("/api/summary")
def summary():
    s = data.sales().merge(data.products(), left_on="product_id", right_on="id")
    s["rev"] = s["units"] * s["price"]
    daily = s.groupby("date")["rev"].sum().tail(60)
    cat = s.groupby(["date", "category"])["rev"].sum().unstack().tail(60)
    t = table()
    return dict(dates=[d.strftime("%Y-%m-%d") for d in daily.index], revenue=[round(v) for v in daily.values],
                categories={c: [round(v) for v in cat[c].values] for c in cat.columns},
                kpis=dict(revenue_30d=round(s[s.date > s.date.max() - __import__("pandas").Timedelta(days=30)]["rev"].sum()),
                          units_30d=int(s[s.date > s.date.max() - __import__("pandas").Timedelta(days=30)]["units"].sum()),
                          at_risk=sum(r["status"] == "Stockout risk" for r in t), overstock=sum(r["status"] == "Overstock" for r in t),
                          forecast_revenue_7d=sum(r["forecast_revenue"] for r in t)))

@app.get("/api/inventory")
def inventory(days: int = 7): return table(days)

@app.get("/api/forecast/{pid}")
def product_forecast(pid: int, days: int = 14):
    s = data.sales(); s = s[s.product_id == pid].sort_values("date").tail(30)
    fc = model.forecast(days)[pid]
    import pandas as pd
    fd = [(s["date"].max() + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d") for i in range(days)]
    return dict(hist_dates=[d.strftime("%Y-%m-%d") for d in s["date"]], hist=[int(v) for v in s["units"]],
                fc_dates=fd, forecast=[round(v, 1) for v in fc])

class Scenario(BaseModel):
    promo_category: str | None = None
    footfall_pct: float = 0
    days: int = 7

@app.post("/api/simulate")
def simulate(sc: Scenario):
    base, scen = table(sc.days), table(sc.days, sc.promo_category, sc.footfall_pct)
    tot = lambda t, k: sum(r[k] for r in t)
    return dict(base=dict(revenue=tot(base, "forecast_revenue"), units=tot(base, "forecast_units"), lost=tot(base, "lost_sales"),
                          at_risk=sum(r["status"] == "Stockout risk" for r in base)),
                scenario=dict(revenue=tot(scen, "forecast_revenue"), units=tot(scen, "forecast_units"), lost=tot(scen, "lost_sales"),
                              at_risk=sum(r["status"] == "Stockout risk" for r in scen)), items=scen)

@app.get("/api/recommendations")
def recommendations():
    t, recs = table(), []
    for r in sorted(t, key=lambda r: r["days_cover"]):
        if r["status"] == "Stockout risk":
            recs.append(dict(type="restock", priority="High", text=f"Restock {r['name']}: only {r['days_cover']} days of stock left. Order about {r['reorder_qty']} units."))
    for r in t:
        if r["status"] == "Overstock":
            recs.append(dict(type="promo", priority="Medium", text=f"{r['name']} has {r['days_cover']} days of cover. Run a promotion or pause reordering."))
    top = max(t, key=lambda r: r["forecast_revenue"])
    recs.append(dict(type="insight", priority="Info", text=f"{top['name']} is expected to earn the most next week (about ₹{top['forecast_revenue']:,}). Keep it at eye level and fully stocked."))
    return recs
