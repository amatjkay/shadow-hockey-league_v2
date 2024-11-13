from flask import Flask, render_template
from data.managers_data import managers, countries

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', managers=managers, countries=countries)

if __name__ == '__main__':
    app.run(debug=True)