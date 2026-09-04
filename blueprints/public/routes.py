from datetime import date
from flask import Blueprint, render_template, request, abort, redirect, url_for

from extensions import db, cache
from models import Post, Category, PostSlugHistory
from utils import render_markdown, now_ist

public_bp = Blueprint("public", __name__, template_folder="../../templates/public")


def _published_query():
    return Post.query.filter_by(status="published")


@public_bp.route("/")
@cache.cached(timeout=30)
def home():
    hero = _published_query().order_by(Post.published_at.desc()).first()
    latest = _published_query().order_by(Post.published_at.desc()).limit(9).all()
    categories = Category.query.all()
    return render_template("public/home.html", hero=hero, latest=latest, categories=categories)


@public_bp.route("/today")
@cache.cached(timeout=30, query_string=True)
def today():
    today_date = now_ist().date()
    page = request.args.get("page", 1, type=int)
    pagination = (
        _published_query()
        .filter(Post.match_date == today_date)
        .order_by(Post.match_time.asc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template("public/listing.html", pagination=pagination, title="Today's Predictions")


@public_bp.route("/prediction/<slug>")
@cache.cached(timeout=60, unless=lambda: request.args.get("_nocache"))
def article(slug):
    post = Post.query.filter_by(slug=slug).first()
    if not post:
        old = PostSlugHistory.query.filter_by(old_slug=slug).first()
        if old and old.post and old.post.is_published():
            return redirect(url_for("public.article", slug=old.post.slug), code=301)
        abort(404)
    if not post.is_published():
        abort(404)
    content_html = render_markdown(post.content)
    related = (
        _published_query()
        .filter(Post.category_id == post.category_id, Post.id != post.id)
        .order_by(Post.published_at.desc())
        .limit(4)
        .all()
    )
    return render_template("public/article.html", post=post, content_html=content_html, related=related)


@public_bp.route("/category/<slug>")
@cache.cached(timeout=30, query_string=True)
def category(slug):
    cat = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get("page", 1, type=int)
    pagination = (
        _published_query()
        .filter(Post.category_id == cat.id)
        .order_by(Post.published_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template("public/listing.html", pagination=pagination, title=cat.name, category=cat)


@public_bp.route("/archive")
@cache.cached(timeout=60)
def archive():
    posts = _published_query().order_by(Post.published_at.desc()).all()
    grouped = {}
    for p in posts:
        if not p.published_at:
            continue
        key = p.published_at.strftime("%B %Y")
        grouped.setdefault(key, []).append(p)
    return render_template("public/archive.html", grouped=grouped)


@public_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    pagination = None
    if q:
        like = f"%{q}%"
        pagination = (
            _published_query()
            .filter(
                db.or_(
                    Post.title.ilike(like),
                    Post.summary.ilike(like),
                    Post.team_1.ilike(like),
                    Post.team_2.ilike(like),
                    Post.tournament.ilike(like),
                )
            )
            .order_by(Post.published_at.desc())
            .paginate(page=page, per_page=20, error_out=False)
        )
    return render_template("public/search.html", pagination=pagination, q=q)


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/contact")
def contact():
    return render_template("public/contact.html")
