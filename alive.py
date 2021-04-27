from flask import Flask
from threading import Thread
import time

app = Flask(__name__)
start = time.time()
repl = '0.0.0.0'

@app.route('/')
def current():
    return f"Current UPTIME: {time.time() - start}"

def begin():
    app.run(repl, port = 8080)

def suffer():
    server = Thread(target = begin)
    server.start()
