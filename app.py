import os
from datetime import datetime
from flask import Flask, Response, render_template, request

from config import config_map
from extensions import db, bcrypt, csrf, cache, limiter
from models import Post, Category, SiteSetting
from utils import now_ist


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    from blueprints.public.routes import public_bp
    from blueprints.admin.routes import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    register_jinja_helpers(app)
    register_security_headers(app)
    register_error_handlers(app)
    register_seo_routes(app)

    with app.app_context():
        db.create_all()

    return app


def register_jinja_helpers(app):
    @app.context_processor
    def inject_globals():
        return {
            "site_settings": SiteSetting.get(),
            "current_year": now_ist().year,
            "site_url": app.config["SITE_URL"],
            "google_site_verification": app.config["GOOGLE_SITE_VERIFICATION"],
        }

    @app.template_filter("ist_date")
    def ist_date(value, fmt="%d %B %Y"):
        if not value:
            return ""
        return value.strftime(fmt)

    @app.template_filter("ist_time")
    def ist_time(value, fmt="%I:%M %p"):
        if not value:
            return ""
        return value.strftime(fmt)

    @app.template_filter("time_ago")
    def time_ago(value):
        if not value:
            return ""
        # published_at is stored as naive UTC (datetime.utcnow()); compare in the same frame
        seconds = (datetime.utcnow() - value).total_seconds()
        if seconds < 60:
            return "just now"
        minutes = int(seconds // 60)
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        hours = int(minutes // 60)
        if hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = int(hours // 24)
        if days < 30:
            return f"{days} day{'s' if days != 1 else ''} ago"
        months = int(days // 30)
        if months < 12:
            return f"{months} month{'s' if months != 1 else ''} ago"
        years = int(months // 12)
        return f"{years} year{'s' if years != 1 else ''} ago"


def register_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.path.startswith("/admin"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"
            )
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("public/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("public/404.html", message="Uploaded file too large."), 413


def register_seo_routes(app):
    @app.route("/robots.txt")
    def robots_txt():
        lines = [
            "User-agent: *",
            "Disallow: /admin/",
            f"Sitemap: {app.config['SITE_URL']}/sitemap.xml",
        ]
        return Response("\n".join(lines), mimetype="text/plain")

    @app.route("/sitemap.xml")
    @cache.cached(timeout=300)
    def sitemap_xml():
        posts = Post.query.filter_by(status="published").order_by(Post.published_at.desc()).all()
        categories = Category.query.all()
        site_url = app.config["SITE_URL"]

        urls = [
            {"loc": site_url + "/", "lastmod": None},
            {"loc": site_url + "/archive", "lastmod": None},
            {"loc": site_url + "/about", "lastmod": None},
            {"loc": site_url + "/contact", "lastmod": None},
        ]
        for c in categories:
            urls.append({"loc": f"{site_url}/category/{c.slug}", "lastmod": None})
        for p in posts:
            urls.append({
                "loc": f"{site_url}/prediction/{p.slug}",
                "lastmod": (p.updated_at or p.published_at).strftime("%Y-%m-%d") if (p.updated_at or p.published_at) else None,
            })

        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for u in urls:
            xml_parts.append("<url>")
            xml_parts.append(f"<loc>{u['loc']}</loc>")
            if u["lastmod"]:
                xml_parts.append(f"<lastmod>{u['lastmod']}</lastmod>")
            xml_parts.append("</url>")
        xml_parts.append("</urlset>")
        return Response("\n".join(xml_parts), mimetype="application/xml")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
