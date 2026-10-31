# RetailTwin AI

AI-powered digital twin of a retail store: **predict** demand, **simulate** decisions, **optimize** inventory.
BVCOE Navi Mumbai – B.E. project (Guide: Prof. Mahesh Bhule).

## Tech stack (as in the synopsis)
| Layer | Technology |
|---|---|
| Frontend | React.js + Vite + Tailwind CSS |
| Backend | Python + FastAPI |
| AI/ML | Pandas, NumPy, Scikit-learn, XGBoost |
| Database | PostgreSQL (SQLite is used by default so it runs with no setup) |
| Visualization | Plotly |

## Run it
**1. Backend** (terminal 1)
```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
On first start it creates ~2,100 days of synthetic sales rows (12 products x 180 days), saves them in the database and trains the XGBoost model. API docs: http://localhost:8000/docs

**2. Frontend** (terminal 2)
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

**Use PostgreSQL instead of SQLite:** create a database, then set
`DATABASE_URL=postgresql://user:password@localhost:5432/retailtwin` before starting the backend.

## What is done (about 50%)
- Data layer: products and sales tables, synthetic data with weekly pattern, growth trend and promotions
- Forecasting: XGBoost model with lag and rolling-average features, recursive 7 to 14 day forecast, compared against a 7-day moving-average baseline (MAE and RMSE shown on the dashboard)
- Inventory analysis: days of cover, stockout risk, overstock, reorder quantity, lost-sales estimate
- What-if simulation: promotion on a category and footfall change, with revenue impact
- Smart recommendations: restock, promote, and top-seller insights
- Dashboard: KPIs, sales chart, forecast chart, inventory table
- Live store twin: simulated shoppers, foot-traffic heatmap and live stock on a store floor map

## Still to do (remaining 50%)
- Upload and use real or public retail data (CSV import, M5 dataset)
- Customer segmentation and buying-pattern insights
- Hyperparameter tuning and more features (weather, holidays, price changes)
- User login, multiple stores and saved scenarios
- Automated tests and deployment

## API
`GET /api/summary` `GET /api/inventory` `GET /api/forecast/{product_id}` `GET /api/model/metrics` `GET /api/recommendations` `POST /api/simulate`
file:///C:/Users/bhong/OneDrive/Desktop/RetailTwiinAI/RetailTwin-AI.html

