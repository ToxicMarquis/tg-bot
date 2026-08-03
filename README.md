# Telegram-бот для приёма заявок

Бот на **aiogram 3.x**: собирает заявку (адрес, телефон, вид работ), даёт клиенту
выбрать свободное «окошко» из расписания и отправляет заявку администратору.
За 24 часа до забронированного времени админу приходит напоминание.

Данные хранятся в SQLite, напоминания планирует APScheduler. Умеет работать
через прокси на Cloudflare Workers, если сервер не достаёт до `api.telegram.org`.

## Сценарий клиента

1. `/start`
2. **Адрес**
3. **Телефон** (вручную или кнопкой «Отправить свой номер»)
4. **Вид работ**
5. **Время** – inline-кнопки со свободными окошками. Забронированное окошко
   сразу пропадает у остальных. Можно выбрать «Согласовать по телефону»
6. Проверка заявки и подтверждение → заявка уходит админу

На каждом шаге есть «❌ Отменить» и команда `/cancel`.

## Панель администратора

Команда `/admin` (доступна только для ID из `ADMIN_ID`):

- **➕ Добавить окошки** – список дат, по одному окошку в строке:
  ```
  04.08 10:00
  04.08 14:30
  05.08.2026 09:00
  ```
  Год можно не указывать – возьмётся ближайший. Прошедшие даты и дубликаты
  отбрасываются, о чём бот сообщит.
- **📅 Окошки** – ближайшие окошки со статусом (🟢 свободно / 🔴 занято),
  свободные можно удалить кнопкой.
- **📋 Заявки** – последние заявки с временем, адресом и телефоном.

## Напоминания

За 24 часа до начала забронированного окошка админ получает сообщение
«⏰ Напоминание: заявка завтра» со всеми данными.

Как это устроено:

- источник правды – таблица `applications` в SQLite, а не память планировщика;
- при старте бот вычитывает все брони с `reminded = 0` и ставит задачи заново,
  поэтому перезапуск (`systemctl restart tgbot`) ничего не теряет;
- если бот лежал в момент напоминания, оно уйдёт сразу после старта;
- каждые 15 минут работает подметающая задача – страховка от потерянных задач;
- если бронь оформлена меньше чем за 24 часа до времени, отдельное напоминание
  не отправляется: админ и так только что получил заявку;
- после успешной отправки заявка помечается `reminded = 1`, поэтому дубликатов
  не будет даже при нескольких перезапусках.

Почему APScheduler, а не `asyncio.sleep` в фоне: задачи переживают рестарт (мы
восстанавливаем их из БД), есть `misfire_grace_time` для пропущенных срабатываний
и один общий планировщик вместо сотен висящих корутин. APScheduler 4.x пока
в альфе – используется ветка 3.x с `AsyncIOScheduler`.

## Структура базы данных

Файл БД создаётся автоматически при первом запуске (`DB_PATH`, по умолчанию `bot.db`).

```sql
slots
  id          INTEGER PRIMARY KEY
  starts_at   TEXT UNIQUE      -- ISO, локальное время (TIMEZONE)
  is_booked   INTEGER          -- 0 свободно / 1 занято
  created_at  TEXT

applications
  id          INTEGER PRIMARY KEY
  slot_id     INTEGER UNIQUE REFERENCES slots(id)   -- NULL = время по договорённости
  user_id     INTEGER
  username    TEXT
  full_name   TEXT
  address     TEXT
  phone       TEXT
  service     TEXT
  created_at  TEXT
  reminded    INTEGER          -- 1 = напоминание уже отправлено
```

Бронирование атомарное: `UPDATE slots SET is_booked = 1 WHERE id = ? AND is_booked = 0`.
Если двое подтвердят одно окошко одновременно, второй получит предложение
выбрать другое время, а не молчаливую перезапись.

## Структура проекта

```
bot.py             точка входа: конфиг, БД, планировщик, long polling
config.py          загрузка настроек из .env
db.py              SQLite: схема, слоты, заявки
reminders.py       APScheduler и логика напоминаний
timeutils.py       часовой пояс, разбор и форматирование дат
texts.py           тексты сообщений и карточка заявки
states.py          состояния FSM
keyboards.py       клавиатуры и callback data
validators.py      проверка адреса, телефона и вида работ
handlers/
├── __init__.py    сборка роутеров
├── common.py      /cancel, /help
├── admin.py       /admin: окошки и заявки
└── application.py сценарий заявки
cloudflare/        прокси к api.telegram.org
deploy/            юнит systemd
```

## Установка

Нужен Python 3.10 или новее.

```bash
git clone https://github.com/mrq8/tg-bot.git
cd tg-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Обновление на сервере

```bash
cd /root/tg-bot
git pull
.venv/bin/pip install -r requirements.txt
systemctl restart tgbot
journalctl -u tgbot -f
```

Новые зависимости: `aiosqlite` и `APScheduler`. Файл БД появится рядом с
`WorkingDirectory` из юнита (`/root/tg-bot/bot.db`), отдельная настройка не нужна.

## Настройки (.env)

| Переменная         | Обязательна | Описание                                                                                      |
|--------------------|-------------|-----------------------------------------------------------------------------------------------|
| `BOT_TOKEN`        | да          | Токен бота от [@BotFather](https://t.me/BotFather)                                              |
| `ADMIN_ID`         | да          | Telegram ID администратора ([@userinfobot](https://t.me/userinfobot)). Несколько – через запятую |
| `TIMEZONE`         | нет         | Часовой пояс расписания и напоминаний, по умолчанию `Europe/Moscow`                              |
| `TELEGRAM_API_URL` | нет         | Базовый адрес прокси. Если пусто – бот ходит напрямую в `api.telegram.org`                       |
| `DB_PATH`          | нет         | Путь к файлу SQLite, по умолчанию `bot.db`                                                       |

> **Важно:** администратор должен сам хотя бы раз написать боту `/start` –
> иначе Telegram не разрешит боту отправлять ему сообщения.

## Автозапуск (systemd)

Юнит лежит в `deploy/tgbot.service`:

```bash
cp deploy/tgbot.service /etc/systemd/system/tgbot.service
systemctl daemon-reload
systemctl enable --now tgbot
```

## Прокси через Cloudflare Workers

Воркер принимает запросы бота и переадресует их в `api.telegram.org`.
Бесплатного тарифа Cloudflare хватает с запасом (100 000 запросов в сутки).

Чтобы воркер не стал открытым релеем для чужих ботов, он отвечает только на
запросы с секретным префиксом в пути: `https://<воркер>/<секрет>/bot<токен>/<метод>`.

### 1. Придумайте секрет

```bash
openssl rand -hex 16
```

### 2. Разверните воркер

**Вариант А – через консоль (wrangler).** Нужен Node.js 18+ на любой машине
с доступом к Cloudflare, необязательно на сервере с ботом:

```bash
cd cloudflare
npx wrangler login
npx wrangler secret put PROXY_SECRET
npx wrangler deploy
```

**Вариант Б – через панель Cloudflare.** Workers & Pages → Create → Start with
Hello World → Deploy. Затем Edit code, вставьте содержимое `cloudflare/worker.js`,
задеплойте. После этого Settings → Variables and Secrets → Add → тип Secret,
имя `PROXY_SECRET`, значение – секрет из шага 1.

### 3. Проверьте прокси

```bash
curl "https://tg-api-proxy.<субдомен>.workers.dev/<секрет>/bot<ТОКЕН>/getMe"
```

Ответ должен содержать `"ok":true`. Если пришло `Not found` – не совпадает
секрет, если `PROXY_SECRET is not configured` – переменная не задана.

### 4. Пропишите адрес в .env

```env
TELEGRAM_API_URL=https://tg-api-proxy.<субдомен>.workers.dev/<секрет>
```

Без завершающего слэша и без `/bot...` – бот сам добавит токен и метод.

### Если домен workers.dev недоступен

Привяжите к воркеру свой домен, обслуживаемый Cloudflare: Workers & Pages →
воркер → Settings → Domains & Routes → Add → Custom domain. Затем укажите
`TELEGRAM_API_URL=https://tg.example.com/<секрет>`.

## Примечания

- FSM-состояния живут в `MemoryStorage`: незаконченные анкеты сбрасываются при
  перезапуске, но слоты, заявки и напоминания хранятся в SQLite и не теряются.
- Бот работает в режиме long polling, вебхук и белый IP не требуются.
- `.env` и `*.db` добавлены в `.gitignore` – не коммитьте токен и базу.
- Бэкап базы: `sqlite3 bot.db ".backup backup.db"` или просто копирование файла
  при остановленном боте.
