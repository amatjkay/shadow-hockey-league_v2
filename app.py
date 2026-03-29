from flask import Flask, redirect, render_template, url_for
from data.rating import build_leaderboard

app = Flask(__name__)


@app.route('/')
def index():
    try:
        return render_template(
            'index.html',
            rating_rows=build_leaderboard(),
        )
    except Exception as e:
        print(f'Error: {str(e)}')
        return render_template('error.html'), 500


@app.route('/rating')
def rating():
    """Старый адрес: ведёт на главную, блок рейтинга."""
    return redirect(url_for('index') + '#rating', code=308)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    app.run(debug=True, port=args.port)