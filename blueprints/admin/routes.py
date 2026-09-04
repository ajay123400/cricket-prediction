from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app

from extensions import db, bcrypt, limiter, cache
from models import User, Post, Category, SiteSetting, PostSlugHistory
from utils import unique_slug, save_uploaded_image, now_ist

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes", methods=["POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session.clear()
            session["admin_id"] = user.id
            session["admin_username"] = user.username
            next_url = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_url)
        flash("Invalid username or password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    today_date = now_ist().date()
    month_start = today_date.replace(day=1)

    total_posts = Post.query.count()
    published = Post.query.filter_by(status="published").count()
    drafts = Post.query.filter_by(status="draft").count()
    today_posts = Post.query.filter(db_func_date_created(today_date)).count()
    month_posts = Post.query.filter(Post.created_at >= datetime(month_start.year, month_start.month, month_start.day)).count()

    recent = Post.query.order_by(Post.created_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total_posts=total_posts,
        published=published,
        drafts=drafts,
        today_posts=today_posts,
        month_posts=month_posts,
        recent=recent,
    )


def db_func_date_created(today_date):
    return db.func.date(Post.created_at) == today_date.isoformat()


@admin_bp.route("/posts")
@login_required
def posts_list():
    status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    query = Post.query
    if status_filter in ("draft", "published"):
        query = query.filter_by(status=status_filter)
    pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/posts.html", pagination=pagination, status_filter=status_filter)


@admin_bp.route("/posts/draft")
@login_required
def posts_draft():
    return redirect(url_for("admin.posts_list", status="draft"))


def _apply_post_form(post, form, files, app_config):
    post.title = form.get("title", "").strip()
    post.match_name = form.get("match_name", "").strip()
    post.team_1 = form.get("team_1", "").strip()
    post.team_2 = form.get("team_2", "").strip()

    match_date = form.get("match_date")
    post.match_date = datetime.strptime(match_date, "%Y-%m-%d").date() if match_date else None

    match_time = form.get("match_time")
    post.match_time = datetime.strptime(match_time, "%H:%M").time() if match_time else None

    post.tournament = form.get("tournament", "").strip()
    post.venue = form.get("venue", "").strip()

    category_id = form.get("category_id")
    post.category_id = int(category_id) if category_id else None

    post.prediction = form.get("prediction") or None
    t1p = form.get("team_1_probability")
    t2p = form.get("team_2_probability")
    post.team_1_probability = int(t1p) if t1p else None
    post.team_2_probability = int(t2p) if t2p else None
    post.confidence = form.get("confidence") or None

    post.summary = form.get("summary", "").strip()
    post.content = form.get("content", "")

    post.seo_title = form.get("seo_title", "").strip()
    post.seo_description = form.get("seo_description", "").strip()
    post.seo_keywords = form.get("seo_keywords", "").strip()

    image_file = files.get("featured_image")
    if image_file and image_file.filename:
        filename = save_uploaded_image(
            image_file,
            app_config["UPLOAD_FOLDER"],
            app_config["ALLOWED_IMAGE_EXTENSIONS"],
            app_config["MAX_UPLOAD_MB"],
        )
        post.featured_image = filename


@admin_bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def post_new():
    categories = Category.query.all()

    if request.method == "POST":
        post = Post(status="draft")
        try:
            _apply_post_form(post, request.form, request.files, current_app.config)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("admin/post_form.html", post=post, categories=categories)

        post.slug = unique_slug(db.session, Post, post.title)

        action = request.form.get("action")
        if action == "publish":
            post.status = "published"
            post.published_at = datetime.utcnow()
        else:
            post.status = "draft"

        db.session.add(post)
        db.session.commit()
        cache.clear()
        flash("Post saved.", "success")
        return redirect(url_for("admin.posts_list"))

    return render_template("admin/post_form.html", post=None, categories=categories)


@admin_bp.route("/posts/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def post_edit(post_id):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.all()

    if request.method == "POST":
        old_title = post.title
        try:
            _apply_post_form(post, request.form, request.files, current_app.config)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("admin/post_form.html", post=post, categories=categories)

        if post.title != old_title:
            old_slug = post.slug
            post.slug = unique_slug(db.session, Post, post.title, exclude_id=post.id)
            if old_slug != post.slug and post.status == "published":
                if not PostSlugHistory.query.filter_by(old_slug=old_slug).first():
                    db.session.add(PostSlugHistory(post_id=post.id, old_slug=old_slug))

        action = request.form.get("action")
        if action == "publish" and post.status != "published":
            post.status = "published"
            post.published_at = datetime.utcnow()
        elif action == "publish":
            post.status = "published"
        elif action == "save_draft":
            post.status = "draft"

        db.session.commit()
        cache.clear()
        flash("Post updated.", "success")
        return redirect(url_for("admin.posts_list"))

    return render_template("admin/post_form.html", post=post, categories=categories)


@admin_bp.route("/posts/delete/<int:post_id>", methods=["POST"])
@login_required
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    cache.clear()
    flash("Post deleted.", "success")
    return redirect(url_for("admin.posts_list"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            cat = Category(name=name, slug=unique_slug(db.session, Category, name))
            db.session.add(cat)
            db.session.commit()
            cache.clear()
            flash("Category added.", "success")
        return redirect(url_for("admin.categories"))

    all_categories = Category.query.all()
    return render_template("admin/categories.html", categories=all_categories)


@admin_bp.route("/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    cache.clear()
    flash("Category deleted.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    site_settings = SiteSetting.get()
    if request.method == "POST":
        action = request.form.get("action")

        if action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            user = User.query.get(session["admin_id"])
            if not bcrypt.check_password_hash(user.password_hash, current_password):
                flash("Current password is incorrect.", "error")
            elif len(new_password) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new_password != confirm_password:
                flash("New password and confirmation do not match.", "error")
            else:
                user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
                db.session.commit()
                flash("Password changed successfully.", "success")
            return redirect(url_for("admin.settings"))

        site_settings.site_name = request.form.get("site_name", "").strip()
        site_settings.description = request.form.get("description", "").strip()
        site_settings.telegram_url = request.form.get("telegram_url", "").strip()
        site_settings.contact_email = request.form.get("contact_email", "").strip()
        db.session.commit()
        cache.clear()
        flash("Settings updated.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", site_settings=site_settings)
