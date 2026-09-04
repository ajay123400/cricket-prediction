"""Initialize the database, create the admin account, and (optionally) seed sample content.

Usage:
    python seed.py            # create tables + admin user only
    python seed.py --sample   # also insert dummy TESTING-ONLY predictions
"""
import sys
from datetime import datetime, timedelta, date, time

from app import create_app
from extensions import db, bcrypt
from models import User, Category, Post, SiteSetting
from utils import unique_slug


def seed_admin(app):
    with app.app_context():
        db.create_all()
        username = app.config["ADMIN_USERNAME"]
        password = app.config["ADMIN_PASSWORD"]

        if User.query.filter_by(username=username).first():
            print(f"Admin user '{username}' already exists. Skipping.")
            return

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        admin = User(username=username, password_hash=password_hash)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user '{username}' created.")

        SiteSetting.get()


def seed_sample(app):
    with app.app_context():
        cat_names = ["IPL", "International", "T20", "ODI", "Test", "Domestic", "Women's Cricket", "Other"]
        categories = {}
        for name in cat_names:
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(name=name, slug=unique_slug(db.session, Category, name))
                db.session.add(cat)
                db.session.flush()
            categories[name] = cat
        db.session.commit()

        if Post.query.first():
            print("Sample posts already exist. Skipping sample content.")
            return

        sample_content = """## Recent Form
[TESTING ONLY] Team 1 has won 4 of their last 5 matches, showing strong batting depth.

## Head to Head
[TESTING ONLY] Historically evenly matched with a slight edge to Team 1 in recent encounters.

## Venue Analysis
[TESTING ONLY] This venue traditionally favors batting-first sides under lights.

## Pitch Report
[TESTING ONLY] A balanced surface expected with some assistance for pace bowlers early on.

## Key Players
[TESTING ONLY] Watch out for the in-form top order batter and the death-overs specialist.

## Final Verdict
[TESTING ONLY] This is dummy development data, not a real prediction.
"""

        samples = [
            dict(title="India vs Australia Match Prediction", team_1="India", team_2="Australia",
                 category="IPL", prediction="team_1", t1p=63, t2p=37, confidence="medium", days=0),
            dict(title="England vs New Zealand Match Prediction", team_1="England", team_2="New Zealand",
                 category="International", prediction="team_2", t1p=45, t2p=55, confidence="high", days=-1),
            dict(title="Mumbai Indians vs Chennai Super Kings Prediction", team_1="Mumbai Indians", team_2="Chennai Super Kings",
                 category="IPL", prediction="team_1", t1p=58, t2p=42, confidence="low", days=-2),
        ]

        for s in samples:
            title = "[TEST DATA] " + s["title"]
            post = Post(
                title=title,
                summary="[TESTING ONLY] Development sample prediction — not real content.",
                content=sample_content,
                match_name=s["title"],
                team_1=s["team_1"],
                team_2=s["team_2"],
                match_date=date.today() + timedelta(days=s["days"]),
                match_time=time(19, 30),
                tournament=s["category"],
                venue="Sample Stadium",
                category_id=categories[s["category"]].id,
                prediction=s["prediction"],
                team_1_probability=s["t1p"],
                team_2_probability=s["t2p"],
                confidence=s["confidence"],
                status="published",
                seo_title=title,
                seo_description="[TESTING ONLY] Sample SEO description.",
                published_at=datetime.utcnow() - timedelta(days=-s["days"]),
            )
            post.slug = unique_slug(db.session, Post, post.title)
            db.session.add(post)

        db.session.commit()
        print("Sample TESTING-ONLY predictions created.")


if __name__ == "__main__":
    app = create_app()
    seed_admin(app)
    if "--sample" in sys.argv:
        seed_sample(app)
