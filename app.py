from flask import Flask
from routes.auth_routes import auth
from database.database import init_db
from routes.resume_routes import resume
from routes.analyzer_routes import analyzer

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = "novus_secret_key"

init_db()

app.register_blueprint(auth)
app.register_blueprint(resume)
app.register_blueprint(analyzer)

if __name__ == "__main__":
    app.run(debug=True)