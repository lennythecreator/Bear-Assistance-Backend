from flask import Flask
import psycopg2 

app = Flask(__name__)

@app.route("/")

def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname = "BearAssitstance",
            user="",
            password = "your_db_password",
            host="localhost",
            port =""
        )
        print("DB connection successful")
        return connection
def hello_world():
    return "<p>Hello, World!</p>"