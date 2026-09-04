from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)

    posts = db.relationship("Post", backref="category", lazy="dynamic")


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)  # stored as Markdown, sanitized on render

    match_name = db.Column(db.String(255))
    team_1 = db.Column(db.String(120))
    team_2 = db.Column(db.String(120))
    match_date = db.Column(db.Date)
    match_time = db.Column(db.Time)  # stored as IST wall-clock time
    tournament = db.Column(db.String(150))
    venue = db.Column(db.String(200))

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    prediction = db.Column(db.String(20))  # team_1 / team_2 / draw / no_result
    team_1_probability = db.Column(db.Integer)
    team_2_probability = db.Column(db.Integer)
    confidence = db.Column(db.String(10))  # low / medium / high

    featured_image = db.Column(db.String(255))

    status = db.Column(db.String(10), default="draft", index=True)  # draft / published

    seo_title = db.Column(db.String(255))
    seo_description = db.Column(db.String(400))
    seo_keywords = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)

    def is_published(self):
        return self.status == "published"


class PostSlugHistory(db.Model):
    __tablename__ = "post_slug_history"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    old_slug = db.Column(db.String(255), unique=True, nullable=False, index=True)

    post = db.relationship("Post", backref=db.backref("old_slugs", cascade="all, delete-orphan"))


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(120), default="Cricket Predictions")
    logo = db.Column(db.String(255))
    description = db.Column(db.String(400))
    telegram_url = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))

    @staticmethod
    def get():
        settings = SiteSetting.query.first()
        if not settings:
            settings = SiteSetting(site_name="Cricket Predictions")
            db.session.add(settings)
            db.session.commit()
        return settings
