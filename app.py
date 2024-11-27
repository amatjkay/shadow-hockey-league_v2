from flask import Flask, render_template
from data.managers_data import managers

app = Flask(__name__)

@app.route('/')
def index():
    try:
        return render_template('index.html', managers=managers)
    except Exception as e:
        print(f'Error: {str(e)}')
        return render_template('error.html'), 500

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    app.run(debug=True, port=args.port)