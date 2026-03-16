import os
import sys
import logging
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("FLASK_ENV", "production")

log_path = os.path.join(BASE_DIR, "wsgi_error.log")
handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))

from app import create_app
application = create_app()

if not application.logger.handlers:
    application.logger.addHandler(handler)
application.logger.setLevel(logging.INFO)
application.logger.info("Passenger levantó AgroDesk")