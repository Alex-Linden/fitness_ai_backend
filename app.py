from flask import Flask

app = Flask(__name__)

@app.get('/hello')
def say_hello():
    """Return simple "Hello" Greeting."""
    html = "<html><body><h1>Hello</h1></body></html>"
    return html