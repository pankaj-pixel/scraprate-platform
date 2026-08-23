# ScrapRate — FastAPI + React MVP

A modern homepage for a scrap-price intelligence platform. It includes dynamic city-wise scrap rates, 30-day price charts, search/filtering, material detail modals, market ranges and an API foundation for a future buy/sell marketplace.

> Current prices are intentionally **demo/generated data**. Do not present them as real market prices. Replace the demo price engine with verified market sources before production.

## 1. Configure MySQL 8+

Create a MySQL database and application user, then copy the environment template:

```bash
cd backend
cp .env.example .env
```

Using the MySQL client as an administrator, create the local database and a dedicated application user (replace the password placeholder first):

```sql
CREATE DATABASE scraprate
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'scraprate_user'@'localhost'
  IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';

GRANT ALL PRIVILEGES ON scraprate.*
  TO 'scraprate_user'@'localhost';

FLUSH PRIVILEGES;
```

Set the matching `DATABASE_URL` in `.env`; URL-encode special characters in the password. Do not commit that file. Apply the schema and load the idempotent demo dataset:

```bash
python -m alembic upgrade head
python -m app.seed
```

The seed command stores dated demo observations in MySQL. It only inserts missing dates and never deletes historical prices.

## 2. Run backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

FastAPI docs: `http://localhost:8000/docs`

## 3. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Main API endpoints

- `GET /api/materials?city=Delhi`
- `GET /api/materials/copper?city=Delhi`
- `GET /api/materials/copper/history?city=Delhi&days=30`
- `GET /api/market-overview?city=Delhi`
- `GET /api/cities`

## Price data status

The API now reads materials and dated price history from MySQL. The included seed remains generated demo data and is explicitly stored with `is_demo=true`; replace it with verified ingestion sources before presenting prices as real market quotes.
