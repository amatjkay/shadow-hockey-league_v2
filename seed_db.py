from app import create_app
from models import db, Country, Manager, Achievement
from data.managers_data import managers as initial_managers, LEAGUES

def seed_database():
    app = create_app()
    with app.app_context():
        # Очищаем существующие данные
        db.session.query(Achievement).delete()
        db.session.query(Manager).delete()
        db.session.query(Country).delete()
        db.session.commit()

        # Словарь для отслеживания стран
        country_cache = {}

        for manager_data in initial_managers:
            # Получаем или создаем страну
            country_path = manager_data.country
            if country_path not in country_cache:
                country_code = country_path.split('/')[-1].split('.')[0].upper()
                country = Country(
                    code=country_code,
                    flag_path=country_path
                )
                db.session.add(country)
                db.session.flush()
                country_cache[country_path] = country

            # Создаем менеджера
            manager = Manager(
                name=manager_data.name,
                country_id=country_cache[country_path].id
            )
            db.session.add(manager)
            db.session.flush()

            # Добавляем достижения
            for achievement_html in manager_data.achievements:
                # Парсим HTML строку достижения
                import re
                if 'toxic' in achievement_html:
                    achievement = Achievement(
                        type='TOXIC',
                        league=LEAGUES['PRIMARY'],
                        season='N/A',
                        title='Toxic and unpleasant person',
                        icon_path='/static/img/cups/toxic.png',
                        manager_id=manager.id
                    )
                else:
                    match = re.search(r'cups/(.*?)\.(svg|png).*?Shadow (.*?) league (.*?) s(.*?)"', achievement_html)
                    if match:
                        cup_type, ext, league, title, season = match.groups()
                        achievement = Achievement(
                            type=cup_type.upper(),
                            league=league,
                            season=season,
                            title=title,
                            icon_path=f'/static/img/cups/{cup_type}.{ext}',
                            manager_id=manager.id
                        )
                        db.session.add(achievement)

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database() 