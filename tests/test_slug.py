from extensions import db
from models import Post
from utils import unique_slug, slugify


def test_slugify_basic():
    assert slugify("India vs Australia Match Prediction!") == "india-vs-australia-match-prediction"


def test_unique_slug_collision(app):
    with app.app_context():
        p1 = Post(title="India vs Australia", status="draft")
        p1.slug = unique_slug(db.session, Post, "India vs Australia")
        db.session.add(p1)
        db.session.commit()
        assert p1.slug == "india-vs-australia"

        p2 = Post(title="India vs Australia", status="draft")
        p2.slug = unique_slug(db.session, Post, "India vs Australia")
        db.session.add(p2)
        db.session.commit()
        assert p2.slug == "india-vs-australia-2"

        # editing p1 itself should keep its own slug, not collide with itself
        same_slug = unique_slug(db.session, Post, "India vs Australia", exclude_id=p1.id)
        assert same_slug == "india-vs-australia"
