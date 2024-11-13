from pathlib import Path
import unittest

def verify_static_files():
    static_dir = Path('static')
    missing_files = []
    
    # Проверка файлов достижений
    for cup in ['top1', 'top2', 'top3', 'best-reg', 'clap', 'clap-b', 'toxic']:
        ext = 'png' if cup == 'toxic' else 'svg'
        if not (static_dir / 'img' / 'cups' / f'{cup}.{ext}').exists():
            missing_files.append(f'cups/{cup}.{ext}')
    
    # Проверка флагов
    for flag in ['rus', 'bel', 'kz', 'vietnam', 'ua', 'mexico', 'pol', 'china', 'shit']:
        if not (static_dir / 'img' / 'flags' / f'{flag}.png').exists():
            missing_files.append(f'flags/{flag}.png')
    
    # Проверка основных файлов
    required_files = [
        'img/logo.png',
        'img/social/telegram.png',
        'css/style.css',
        'img/favicon/favicon.ico',
        'img/geoloc.svg'
    ]
    
    for file in required_files:
        if not (static_dir / file).exists():
            missing_files.append(file)
    
    return missing_files

class TestVerifyPaths(unittest.TestCase):
    def test_verify_static_files(self):
        missing = verify_static_files()
        self.assertIsInstance(missing, list, "Функция должна возвращать список")
        
    def test_static_directory_exists(self):
        self.assertTrue(Path('static').exists(), "Директория static должна существовать")

if __name__ == '__main__':
    missing = verify_static_files()
    if missing:
        print("❌ Отсутствуют следующие файлы:")
        for file in missing:
            print(f"  - {file}")
    else:
        print("✅ Все файлы на месте!")