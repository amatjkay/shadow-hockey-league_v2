from flask import Flask, render_template
from data.managers_data import managers, countries

app = Flask(__name__)

@app.route('/')
def index():
    try:
        return render_template('index.html', managers=managers, countries=countries)
    except Exception as e:
        app.logger.error(f"Ошибка при рендеринге главной страницы: {str(e)}")
        return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True)