# Cricket Predictions Website

A Flask-based cricket match prediction & analysis website. Admin writes/publishes
predictions from a protected admin panel; visitors read them with no login required.

## Stack
Python 3.11+, Flask 3, SQLAlchemy + SQLite, session-based admin auth (Flask-Bcrypt),
Flask-WTF (CSRF), Flask-Limiter (rate limiting), Flask-Caching, gunicorn (production).

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements-dev.txt   # includes pytest; use requirements.txt for prod-only

copy .env.example .env       # Windows: copy, macOS/Linux: cp
# edit .env: set SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

python seed.py                # creates DB tables + admin user
python seed.py --sample       # optional: also adds TESTING-ONLY dummy predictions

python app.py                 # http://127.0.0.1:5000
```

Admin panel: `http://127.0.0.1:5000/admin/login`

## Running Tests

```bash
pytest -q
```

Covers: slug generation/uniqueness, admin auth (login/logout/protected routes),
draft vs. published visibility.

## Project Layout

```
app.py                 - app factory, security headers, sitemap.xml/robots.txt
config.py              - environment-based config (dev/prod/testing)
extensions.py          - db, bcrypt, csrf, cache, limiter singletons
models.py              - User, Category, Post, SiteSetting
utils.py               - slugify/unique_slug, IST time, image upload, markdown+sanitize
seed.py                - DB init, admin creation, optional sample content
blueprints/public/     - public site routes (/, /prediction/<slug>, /category/..., ...)
blueprints/admin/      - admin panel routes (/admin/...)
templates/, static/    - Jinja templates and CSS/JS/uploads
tests/                 - pytest suite
```

## Admin Guide (quick)

1. Go to `/admin/login`, sign in.
2. Dashboard shows post counts; click **New Prediction**.
3. Fill match details, prediction %, write content (Markdown supported), upload a
   featured image (jpg/png/webp, max 2MB — auto-converted to WebP).
4. **Save Draft** to keep it private, or **Publish** to make it live immediately.
5. Open the published post, use the **Telegram / WhatsApp / Copy Link** buttons to share.

**Slug/URL note:** the app auto-generates a unique slug from the title on publish. If you
rename a published post's title later, its slug changes too — the old URL automatically
301-redirects to the new one, so previously shared links keep working.

## Deployment (production)

Do not use `python app.py` / `flask run` in production. Use gunicorn behind nginx:

```bash
pip install -r requirements.txt
export FLASK_ENV=production   # or set in your process manager
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
```

Example nginx reverse proxy `server` block:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/CricketPrediction/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Put HTTPS (Let's Encrypt/certbot, or your host's SSL) in front of nginx. No custom domain
is required to deploy initially — deploy on the server's IP/hostname first; once the
client buys a domain, point its DNS A record at the server and update `SITE_URL` in `.env`.

**Testing a real WSGI server locally on Windows:** gunicorn doesn't run on Windows (no
`fork()`). To sanity-check the app under a production-grade server before deploying, use
`waitress` instead (`pip install waitress`):

```bash
python -c "from waitress import serve; from app import create_app; serve(create_app('development'), host='127.0.0.1', port=8000)"
```

This is only for local verification — the actual server still deploys with gunicorn+nginx
as above.

## Backups

See [BACKUP_GUIDE.md](BACKUP_GUIDE.md).

## Handover Checklist

- [ ] Source code (this repo)
- [ ] `.env.example` (copy to `.env`, fill real secrets — never commit `.env`)
- [ ] README.md (this file), BACKUP_GUIDE.md
- [ ] Admin credentials shared securely (not over plain chat/email)
- [ ] Client walkthrough: Login → New Prediction → Write → Save Draft/Publish → Copy Link → Share on Telegram
