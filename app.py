from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

@app.get('/hello')
def say_hello():
    """Return simple "Hello" Greeting."""
    html = "<html><body><h1>Hello</h1></body></html>"
    return html