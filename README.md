# AYUKTA Full-Stack Starter

Responsive saree storefront frontend + FastAPI backend + SQLAlchemy database. This is a new Ayukta-branded implementation using common fashion-commerce patterns, not a copy of KalamKantha's source code or proprietary assets.

## Tech stack
- Frontend: HTML, CSS, JavaScript (responsive, no build step)
- Backend: FastAPI, Pydantic, SQLAlchemy
- Database: SQLite by default; PostgreSQL supported with a PostgreSQL SQLAlchemy URL and appropriate driver
- Auth: JWT bearer tokens, bcrypt password hashes
- API docs: `/docs`
## API overview
- `GET /api/health`
- `GET /api/products?category=Cotton&q=mulmul&featured=true`
- `GET /api/products/{slug}`
- `POST /api/auth/register` `{ "name": "Example", "email": "you@example.com", "password": "at-least-8-chars" }`
- `POST /api/auth/login` `{ "email": "you@example.com", "password": "..." }`
- `GET /api/auth/me` (Bearer token)
- `POST /api/orders` (Bearer token; server calculates prices and decrements stock)
- `GET /api/orders/mine` (Bearer token)
- `POST /api/newsletter` `{ "email": "you@example.com" }`
- Admin routes require an admin bearer token:
  - `GET /api/admin/summary`
  - `GET /api/admin/orders`
  - `PATCH /api/admin/orders/{id}` with `{"status":"confirmed"}` etc.
  - `POST /api/admin/products`
  - `PATCH /api/admin/products/{id}`
  - `DELETE /api/admin/products/{id}` (soft-hide product)

## Before production
This starter is not yet a complete production commerce system. Integrate a real payment gateway (e.g. Razorpay) and verify payment webhooks server-side before marking orders paid; implement proper checkout UI, email/SMS, rate limiting, password reset, refresh/revocation strategy, migrations, logging/monitoring, privacy/terms and shipping/tax calculations. Do not store payment card data. Use PostgreSQL for deployed multi-user production, set strong secrets and explicit CORS origins, configure HTTPS, back up the database, and use licensed product photos. Do not commit `.env` or real credentials.

## Notes
- SQLite database file is created automatically at first backend startup.
- Demo seed data is added only if the product table is empty; admin account is created only if missing.
- Product image URLs are examples and require internet access.
- Frontend cart is stored in localStorage; the API is the source of truth for stock and order prices.
