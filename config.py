import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///agrocloud.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'audios')
    

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "instance", "uploads", "docs")
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB
    ALLOWED_DOC_EXT = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "xlsx"}
    

