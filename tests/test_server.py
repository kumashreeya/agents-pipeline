from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Hello from Flask!</h1><p>If you see this, the server works.</p>'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
