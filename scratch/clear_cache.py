from app import create_app
from services.cache_service import cache


def clear_all_cache():
    app = create_app()
    with app.app_context():
        cache.clear()
        print("All cache cleared successfully!")


if __name__ == "__main__":
    clear_all_cache()
