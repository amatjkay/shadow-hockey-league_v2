import unittest
from app import app
from data.managers_data import Manager, managers, countries

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('Рейтинг лиги', html)
        self.assertIn('Кубки', html)

    def test_rating_redirects_to_main(self):
        response = self.app.get('/rating', follow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 308))
        loc = response.headers.get('Location', '')
        self.assertIn('#rating', loc)

    def test_managers_data(self):
        # Проверка наличия данных
        self.assertTrue(len(managers) > 0)
        self.assertTrue(len(countries) > 0)

        # Проверка структуры данных менеджеров
        for manager in managers:
            self.assertIsInstance(manager, Manager)  # Проверка, что это объект Manager
            self.assertIn('name', vars(manager))  # Используем vars для получения атрибутов
            self.assertIn('country', vars(manager))
            self.assertIn('achievements', vars(manager))
            self.assertIsInstance(manager.achievements, list)

    def test_static_files(self):
        # Проверка доступности статических файлов
        static_files = [
            '/static/img/logo.png',
            '/static/css/style.css',
            '/static/img/cups/top1.svg'
        ]
        for file in static_files:
            response = self.app.get(file)
            self.assertIn(response.status_code, [200, 304])

if __name__ == '__main__':
    unittest.main()