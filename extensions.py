from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
