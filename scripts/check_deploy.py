#!/usr/bin/env python3
"""Check deployment configuration before deploy.

Usage:
    python scripts/check_deploy.py
"""

import os
from pathlib import Path

# Load .env file if exists (for local development)
try:
    from dotenv import load_dotenv
    base_dir = Path(__file__).parent.parent
    env_file = base_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ .env загружен: {env_file}\n")
except ImportError:
    pass


def check():
    """Run deployment checks."""
    errors = []
    warnings = []
    
    print("🔍 Проверка конфигурации деплоя...\n")
    
    # Check DATABASE_URL
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        if not db_url.startswith("sqlite:///"):
            errors.append(f"DATABASE_URL должен начинаться с sqlite:///, получено: {db_url}")
        else:
            # Check if using relative path (warning only)
            db_path = db_url.replace("sqlite:///", "")
            if not db_path.startswith("/"):
                warnings.append(
                    f"DATABASE_URL использует относительный путь: {db_path}\n"
                    f"  Рекомендуется абсолютный путь: sqlite:////home/username/project/dev.db"
                )
            elif not Path(db_path).exists():
                errors.append(f"База данных не найдена: {db_path}")
    else:
        warnings.append("DATABASE_URL не установлен (будет использован путь по умолчанию)")
    
    # Check SECRET_KEY
    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        errors.append("SECRET_KEY не установлен")
    elif secret == "dev-secret-key-change-in-production":
        errors.append("SECRET_KEY использует значение по умолчанию (небезопасно!)")
    elif len(secret) < 32:
        warnings.append(f"SECRET_KEY слишком короткий ({len(secret)} символов, рекомендуется 64)")
    
    # Check FLASK_ENV
    flask_env = os.environ.get("FLASK_ENV", "")
    if not flask_env:
        warnings.append("FLASK_ENV не установлен (будет использован 'development')")
    elif flask_env not in ("development", "production", "testing"):
        errors.append(f"Недопустимое значение FLASK_ENV: {flask_env}")
    
    # Check database file (if using default path)
    if not db_url:
        base_dir = Path(__file__).parent.parent
        db_path = base_dir / "dev.db"
        if not db_path.exists():
            warnings.append(f"База данных не найдена: {db_path}")
    
    # Check requirements.txt exists
    req_path = Path(__file__).parent.parent / "requirements.txt"
    if not req_path.exists():
        errors.append(f"requirements.txt не найден: {req_path}")
    
    # Check WSGI file (if on PythonAnywhere)
    wsgi_path = Path("/var/www/amatjkay_pythonanywhere_com_wsgi.py")
    if wsgi_path.exists():
        wsgi_content = wsgi_path.read_text()
        if "sqlite:///dev.db" in wsgi_content and "project_home" not in wsgi_content:
            errors.append(
                "WSGI файл использует относительный путь к БД!\n"
                "  Измени на: os.environ['DATABASE_URL'] = f'sqlite:///{project_home}/dev.db'"
            )
    
    # Print results
    if errors:
        print("❌ Ошибки конфигурации:")
        for e in errors:
            print(f"  - {e}")
        print()
    
    if warnings:
        print("⚠️ Предупреждения:")
        for w in warnings:
            print(f"  - {w}")
        print()
    
    if not errors and not warnings:
        print("✅ Все проверки пройдены! Готов к деплою.")
        return True
    elif not errors:
        print("✅ Критических ошибок нет. Можно деплоить (с учётом предупреждений).")
        return True
    else:
        print("❌ Исправьте ошибки перед деплоем!")
        return False


if __name__ == "__main__":
    import sys
    success = check()
    sys.exit(0 if success else 1)
