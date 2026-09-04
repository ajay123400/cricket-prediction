import os
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import bleach
import markdown as md
from PIL import Image
from werkzeug.utils import secure_filename

IST = ZoneInfo("Asia/Kolkata")

ALLOWED_TAGS = [
    "p", "div", "br", "strong", "em", "u", "b", "i", "ul", "ol", "li", "h2", "h3", "h4",
    "blockquote", "a", "img", "table", "thead", "tbody", "tr", "th", "td", "hr", "code", "pre", "span",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title"],
    "span": ["class"],
}


def now_ist():
    return datetime.now(IST)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def unique_slug(db_session, model, base_text, exclude_id=None):
    base = slugify(base_text) or "post"
    slug = base
    counter = 2
    while True:
        query = db_session.query(model).filter(model.slug == slug)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def render_markdown(content):
    if not content:
        return ""
    html = md.markdown(content, extensions=["extra", "nl2br"])
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def allowed_image(filename, allowed_exts):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed_exts


def save_uploaded_image(file_storage, upload_folder, allowed_exts, max_mb):
    filename = secure_filename(file_storage.filename or "")
    if not filename or not allowed_image(filename, allowed_exts):
        raise ValueError("Invalid file type. Allowed: " + ", ".join(sorted(allowed_exts)))

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > max_mb * 1024 * 1024:
        raise ValueError(f"File too large. Max {max_mb}MB allowed.")

    os.makedirs(upload_folder, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}.webp"
    dest_path = os.path.join(upload_folder, new_name)

    image = Image.open(file_storage.stream)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGBA")
    else:
        image = image.convert("RGB")
    image.save(dest_path, "WEBP", quality=82, method=6)

    return new_name
