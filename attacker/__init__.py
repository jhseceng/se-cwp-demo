from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from attacker import app
app = Flask(__name__)


