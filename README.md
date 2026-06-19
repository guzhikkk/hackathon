```bash
# Docker
docker-compose up -d

#Запуск без Docker
pip install -r requirements.txt
uvicorn app.main:app --reload

# библиотеки м миграции
pip install -r requirements.txt
alembic revision --autogenerate -m "initial"
alembic upgrade head

# первый админ
python -m app.seed
```

    
#### Регистрация

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "mypassword123",
    "full_name": "Иван Петров"
  }'
```

**Тело запроса:**
| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `email` | string | ✅ | Email пользователя |
| `password` | string | ✅ | Пароль |
| `full_name` | string | ❌ | Полное имя (по-умолчанию `""`) |

**Ответ `201 Created`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Ошибки:**
| Код | Когда |
|-----|-------|
| `409 Conflict` | Email уже зарегистрирован |
| `422 Unprocessable Entity` | Невалидные данные |

---

#### Вход

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "mypassword123"
  }'
```

**Тело запроса:**
| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `email` | string | ✅ | Email |
| `password` | string | ✅ | Пароль |

**Ответ `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Ошибки:**
| Код | Когда |
|-----|-------|
| `401 Unauthorized` | Неверный email или пароль |
| `403 Forbidden` | Пользователь деактивирован |

---

#### Refresh

```bash
curl -X POST http://localhost:8080/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Ответ `200 OK`** — новая пара токенов.

**Ошибки:**
| Код | Когда |
|-----|-------|
| `401 Unauthorized` | Токен невалидный, истёк или пользователь не найден |
| `403 Forbidden` | Пользователь деактивирован |

---

### Как использовать токен

После логина/регистрации добавляй `access_token` в заголовок `Authorization`:

```bash
curl -X GET http://localhost:8080/api/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Users

#### GET /me

```bash
curl http://localhost:8080/api/users/me \
  -H "Authorization: Bearer <token>"
```

**Ответ `200 OK`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Иван Петров",
  "avatar_url": null,
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-01-15T10:30:00"
}
```

---

#### PATCH /me

```bash
curl -X PATCH http://localhost:8080/api/users/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Новое Имя",
    "avatar_url": "https://example.com/photo.jpg"
  }'
```

**Тело запроса** (все поля опциональные):
| Поле | Тип | Описание |
|------|-----|----------|
| `full_name` | string \| null | Новое имя |
| `avatar_url` | string \| null | URL аватарки |

**Ответ `200 OK`** — обновлённый профиль (формат как `/me`).

---

#### DELETE /me

```bash
curl -X DELETE http://localhost:8080/api/users/me \
  -H "Authorization: Bearer <token>"
```

**Ответ:** `204 No Content` (пустое тело).

---

#### Список пользователей

```bash
curl http://localhost:8080/api/users \
  -H "Authorization: Bearer <admin_token>"
```

**Ответ `200 OK`:**
```json
[
  {
    "id": "550e8400-...",
    "email": "user@example.com",
    "full_name": "Иван Петров",
    "avatar_url": null,
    "is_active": true,
    "is_admin": false,
    "created_at": "2025-01-15T10:30:00"
  },
  ...
]
```

**Ошибки:**
| Код | Когда |
|-----|-------|
| `401 Unauthorized` | Нет токена |
| `403 Forbidden` | Пользователь не админ |

---

#### Получить пользователя по ID

```bash
curl http://localhost:8080/api/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <admin_token>"
```

**Ответ `200 OK`** — объект пользователя.

**Ошибки:** `403` (не админ), `404` (не найден), `422` (невалидный UUID).

---

#### Обновить пользователя

```bash
curl -X PATCH http://localhost:8080/api/users/550e8400-... \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Изменённое Имя"}'
```

---

#### Удалить пользователя

```bash
curl -X DELETE http://localhost:8080/api/users/550e8400-... \
  -H "Authorization: Bearer <admin_token>"
```

**Ответ:** `204 No Content`.

---

#### Изменить роль пользователя

```bash
curl -X PATCH http://localhost:8080/api/users/550e8400-.../role \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}'
```

**Тело запроса:**
| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `is_admin` | boolean | ✅ | Назначить / снять админа |

**Ответ `200 OK`** — обновлённый профиль пользователя.

---

### 📁 Files

#### Загрузить файл

```bash
curl -X POST http://localhost:8080/api/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@photo.jpg" \
  -F "folder=avatars"
```

Или через query-параметр:
```bash
curl -X POST "http://localhost:8080/api/files/upload?folder=avatars" \
  -H "Authorization: Bearer <token>" \
  -F "file=@photo.jpg"
```

**Параметры:**
| Параметр | Тип | Обязательное | Описание |
|----------|-----|:---:|----------|
| `file` | file (multipart) | ✅ | Загружаемый файл |
| `folder` | string (query) | ❌ | Папка в bucket (по-умолчанию корень) |

**Ответ `200 OK`:**
```json
{
  "key": "avatars/a1b2c3d4e5f6.jpg",
  "url": "http://localhost:9000/uploads/avatars/a1b2c3d4e5f6.jpg?X-Amz-Algorithm=...",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "size": 245760
}
```

> `key` — уникальный ключ файла в S3, используй его для получения/удаления.
> `url` — presigned URL, доступен без авторизации в течение 1 часа.

**Ошибки:**
| Код | Когда |
|-----|-------|
| `413 Content Too Large` | Файл больше 50 MB |
| `401 Unauthorized` | Нет токена |

---

#### Получить presigned URL файла

```bash
curl http://localhost:8080/api/files/avatars/a1b2c3d4e5f6.jpg \
  -H "Authorization: Bearer <token>"
```

**Ответ `200 OK`:**
```json
{
  "key": "avatars/a1b2c3d4e5f6.jpg",
  "url": "http://localhost:9000/uploads/avatars/a1b2c3d4e5f6.jpg?X-Amz-Algorithm=..."
}
```

---

#### Скачать файл напрямую

```bash
curl -OJ "http://localhost:8080/api/files/avatars/a1b2c3d4e5f6.jpg?download=true" \
  -H "Authorization: Bearer <token>"
```

**Ответ:** бинарные данные файла с заголовком `Content-Disposition: attachment`.

---

#### Удалить файл

```bash
curl -X DELETE http://localhost:8080/api/files/avatars/a1b2c3d4e5f6.jpg \
  -H "Authorization: Bearer <token>"
```

**Ответ `200 OK`:**
```json
{
  "ok": true,
  "message": "File 'avatars/a1b2c3d4e5f6.jpg' deleted"
}
```

---

#### Список файлов

```bash
curl http://localhost:8080/api/files \
  -H "Authorization: Bearer <token>"


curl "http://localhost:8080/api/files?prefix=avatars/" \
  -H "Authorization: Bearer <token>"
```

**Ответ `200 OK`:**
```json
{
  "files": [
    {
      "key": "avatars/a1b2c3d4e5f6.jpg",
      "size": 245760,
      "last_modified": "2025-01-15T10:30:00+00:00"
    },
    {
      "key": "avatars/f6e5d4c3b2a1.png",
      "size": 102400,
      "last_modified": "2025-01-16T14:20:00+00:00"
    }
  ],
  "total": 2
}
```

### 🤖 AI (Искусственный интеллект)

#### Отправить запрос нейросети (GigaChat)

```bash
curl -X POST http://localhost:8080/api/ai/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Расскажи шутку про хакатон",
    "system_prompt": "Ты саркастичный программист",
    "temperature": 0.8,
    "max_tokens": 500,
    "model": "GigaChat"
  }'
```

**Тело запроса:**
| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `message` | string | ✅ | Сообщение/Вопрос для нейросети |
| `system_prompt` | string | ❌ | Системный промпт (роль бота) |
| `temperature` | float | ❌ | Креативность ответа (0.0 - 2.0, по-умолчанию `0.7`) |
| `max_tokens` | int | ❌ | Максимальное число токенов в ответе (по-умолчанию `1000`) |
| `model` | string | ❌ | Название модели (по-умолчанию `GigaChat`) |

**Ответ `200 OK`:**
```json
{
  "response": "На хакатоне выигрывает не тот, кто написал лучший код, а тот, чей костыль дожил до конца презентации."
}
```

**Ошибки:**
| Код | Когда |
|-----|-------|
| `401 Unauthorized` | Нет токена |

---

### 🔧 Мониторинг

| Сервис | URL | Логин |
|--------|-----|-------|
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Метрики приложения | http://localhost:8080/metrics | — |

---

### Admin-панелm

URL: `http://localhost:8080/admin`
---

# Тесты
pytest tests/ -v