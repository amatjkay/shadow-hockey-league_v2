# 🔒 Безопасность - Shadow Hockey League v2

**Версия:** 1.0
**Дата:** 7 апреля 2026 г.
**Статус:** ✅ Production

---

## 📋 Обзор

Этот документ описывает меры безопасности в Shadow Hockey League v2.

**Production:** https://shadow-hockey-league.ru/

---

## 🔐 Аутентификация

### Admin Panel

**Метод:** Session-based authentication (Flask-Login)

**Как работает:**
1. Пользователь вводит логин/пароль
2. Пароль проверяется против hash в БД
3. При успехе - создаётся сессия
4. Сессия хранится в secure cookie

**Создание админа:**
```bash
python scripts/create_admin.py
```

**Best Practices:**
- ✅ Используйте сложные пароли (12+ символов)
- ✅ Меняйте пароль регулярно
- ✅ Не делитесь учётными данными

---

### API Authentication

**Метод:** API Key authentication

**Как работает:**
1. Генерируется API ключ
2. Hash ключа хранится в БД
3. Ключ передаётся в заголовке: `X-API-Key: <key>`
4. При запросе - ключ хешируется и сравнивается с БД

**Создание API ключа:**
```bash
# Через админ-панель
/admin/apikey/
```

**Scopes:**
| Scope | Описание | Доступ |
|-------|----------|--------|
| `read` | Только чтение | GET запросы |
| `write` | Запись | POST/PUT/DELETE |
| `admin` | Полный доступ | Все операции |

**Best Practices:**
- ✅ Храните ключи в секрете
- ✅ Используйте минимальный необходимый scope
- ✅ Регулярно ротируйте ключи
- ✅ Не коммитьте ключи в Git

---

## 🛡️ CSRF Защита

**Метод:** Flask-WTF CSRF Protection

**Что защищено:**
- ✅ Все формы в админ-панели
- ✅ Все POST/PUT/DELETE запросы
- ✅ API endpoints (кроме API Key auth)

**Исключения:**
- API endpoints (используют API Key auth)
- Health check endpoint
- Metrics endpoint

**Как работает:**
1. При загрузке формы генерируется CSRF токен
2. Токен передаётся в скрытом поле формы
3. При отправке - токен проверяется
4. Если токен невалиден - запрос отклоняется (400)

---

## 🔒 Rate Limiting

**Метод:** Flask-Limiter

**Лимиты:**
| Endpoint | Лимит | Период |
|----------|-------|--------|
| API | 100 запросов | 1 минута |
| Admin | 200 запросов | 1 минута |
| Health | 1000 запросов | 1 минута |

**Что происходит при превышении:**
- Возвращается `429 Too Many Requests`
- Запрос логируется
- Ключ может быть заблокирован

**Best Practices:**
- ✅ Используйте разные API ключи для разных клиентов
- ✅ Реализуйте retry с exponential backoff
- ✅ Мониторьте использование ключей

---

## 🔑 Управление секретами

### Хранение секретов

**Где хранятся:**
- ✅ Только в `.env` файле
- ✅ Не коммитятся в Git (`.gitignore`)
- ✅ На сервере - с ограниченными правами

**Какие секреты:**
```bash
SECRET_KEY=<random-secret-key>
API_KEY_SECRET=<random-secret-key>
WTF_CSRF_SECRET_KEY=<random-secret-key>
```

**Генерация секретов:**
```bash
openssl rand -hex 32
```

**Best Practices:**
- ✅ Используйте уникальные секреты для каждого окружения
- ✅ Минимум 32 символа
- ✅ Не передавайте секреты по незащищённым каналам
- ✅ Ротируйте секреты при компрометации

---

## 🔐 Хранение паролей

### Метод хеширования

**Алгоритм:** Werkzeug password hashing (PBKDF2)

**Как работает:**
1. Пароль хешируется при создании
2. Hash сохраняется в БД
3. При вводе - пароль хешируется и сравнивается
4. Оригинальный пароль никогда не хранится

**Пример:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Создание
password_hash = generate_password_hash('my_password')

# Проверка
is_valid = check_password_hash(password_hash, 'my_password')
```

**Best Practices:**
- ✅ Минимальная длина пароля: 12 символов
- ✅ Используйте сложные пароли
- ✅ Не используйте одинаковые пароли

---

## 🌐 SSL/TLS

### HTTPS

**Провайдер:** Let's Encrypt

**Сертификат:**
- ✅ Бесплатный
- ✅ Автоматическое обновление (Certbot)
- ✅ Срок действия: 90 дней
- ✅ Автообновление: каждые 60 дней

**Проверка:**
```bash
# Проверить сертификат
certbot certificates

# Проверить автообновление
systemctl status certbot.timer
```

**Nginx конфигурация:**
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/shadow-hockey-league.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shadow-hockey-league.ru/privkey.pem;
}
```

**HTTP → HTTPS редирект:**
```nginx
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

---

## 📝 Audit Log

### Что логируется

**Действия в админ-панели:**
- ✅ CREATE - создание записей
- ✅ UPDATE - обновление записей
- ✅ DELETE - удаление записей
- ✅ LOGIN - входы в админку
- ✅ FLUSH_CACHE - очистка кэша

**Поля записи:**
```python
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)  # Кто сделал
    action = db.Column(db.String)    # Какое действие
    target_model = db.Column(db.String)  # Какую модель
    target_id = db.Column(db.Integer)  # ID записи
    changes = db.Column(db.JSON)     # Что изменилось
    timestamp = db.Column(db.DateTime)  # Когда
```

**Просмотр логов:**
```
/admin/auditlog/
```

**Retention:** 90 дней

---

## 🔒 Безопасность БД

### SQLite

**Защита:**
- ✅ Файл БД вне web-доступной директории
- ✅ Права доступа: 640 (owner read/write, group read)
- ✅ WAL режим для конкурентного доступа

**Расположение:**
```
/home/shleague/shadow-hockey-league_v2/instance/dev.db
```

**Best Practices:**
- ✅ Регулярные бэкапы (ежедневно + pre-deploy)
- ✅ Ограниченный доступ к файлу БД
- ✅ Рассмотрите миграцию на PostgreSQL для production

---

## 🚨 Response Headers

### Security Headers

**Nginx добавляет:**
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Flask добавляет:**
```python
response.headers['X-Content-Type-Options'] = 'nosniff'
response.headers['X-Frame-Options'] = 'SAMEORIGIN'
response.headers['X-XSS-Protection'] = '1; mode=block'
response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
```

---

## 📊 Мониторинг безопасности

### Что мониторим

- ✅ Неудачные попытки входа (Audit Log)
- ✅ Превышение rate limits (Flask-Limiter)
- ✅ CSRF violations (Flask-WTF)
- ✅ Ошибки аутентификации API (API service)
- ✅ Подозрительные запросы (Nginx logs)

### Где смотреть

```bash
# Audit Log
/admin/auditlog/

# Nginx error log
tail -f /var/log/nginx/error.log

# Gunicorn log
journalctl -u shadow-hockey-league -f

# Failed logins
grep "Failed" /var/log/auth.log
```

---

## 🎯 Security Checklist

### Production Deployment

- [ ] `.env` файл не коммитится
- [ ] Секреты сгенерированы случайно
- [ ] SSL сертификат установлен
- [ ] Rate limiting включен
- [ ] CSRF защита работает
- [ ] Audit Log записывается
- [ ] Бэкапы настроены
- [ ] Firewall настроен
- [ ] SSH ключи защищены
- [ ] Пароли сложные

### Regular Checks

- [ ] Проверка Audit Log
- [ ] Мониторинг rate limit violations
- [ ] Проверка CSRF violations
- [ ] Ротация API ключей
- [ ] Обновление зависимостей
- [ ] Проверка SSL сертификата
- [ ] Тестирование на проникновение

---

## 📞 Reporting Vulnerabilities

Если вы нашли уязвимость:

1. **НЕ создавайте публичный issue**
2. **НЕ коммитьте в Git**
3. Свяжитесь с разработчиком напрямую
4. Опишите уязвимость и шаги воспроизведения
5. Дождитесь исправления

---

## 🔮 Планы

- [ ] Two-factor authentication (2FA)
- [ ] IP whitelisting для админки
- [ ] API key expiration
- [ ] Security headers (CSP, HSTS)
- [ ] Regular security audits
- [ ] Penetration testing

---

**Последнее обновление:** 7 апреля 2026 г.
**Версия:** 1.0
**Статус:** ✅ Production ready
