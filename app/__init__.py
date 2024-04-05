from flask import Flask

app = Flask(__name__, template_folder='templates')
app.secret_key = 'secret_key'
from app import routes
