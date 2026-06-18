import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "careerpilot_secret_key"

    SQLALCHEMY_DATABASE_URI = \
        f"sqlite:///{os.path.join(BASE_DIR,'database','careerpilot.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False