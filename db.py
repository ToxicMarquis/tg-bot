from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
import aiosqlite
import timeutils

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    starts_at TEXT NOT NULL UNIQUE,
    is_booked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER UNIQUE REFERENCES slots(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    service TEXT NOT NULL,
    created_at TEXT NOT NULL,
    reminded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_slots_free ON slots(is_booked, starts_at);
CREATE INDEX IF NOT EXISTS idx_apps_reminded ON applications(reminded, slot_id);
"""


@dataclass(frozen=True)
class Slot:
    id: int
    starts_at: datetime
    is_booked: bool


@dataclass(frozen=True)
class Application:
    id: int
    slot_id: int | None
    starts_at: datetime | None
    user_id: int
    username: str | None
    full_name: str
    address: str
    phone: str
    service: str
    created_at: datetime
    reminded: bool


def _to_slot(row: aiosqlite.Row) -> Slot:
    return Slot(
        id=row["id"],
        starts_at=timeutils.from_iso(row["starts_at"]),
        is_booked=bool(row["is_booked"]),
    )


def _to_application(row: aiosqlite.Row) -> Application:
    return Application(
        id=row["id"],
        slot_id=row["slot_id"],
        starts_at=timeutils.from_iso(row["starts_at"]) if row["starts_at"] else None,
        user_id=row["user_id"],
        username=row["username"],
        full_name=row["full_name"],
        address=row["address"],
        phone=row["phone"],
        service=row["service"],
        created_at=timeutils.from_iso(row["created_at"]),
        reminded=bool(row["reminded"]),
    )


APPLICATION_FIELDS = """
    a.id, a.slot_id, a.user_id, a.username, a.full_name,
    a.address, a.phone, a.service, a.created_at, a.reminded, s.starts_at
"""


class Database:
    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("База данных не подключена")
        return self._conn

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        logger.info("База данных готова: %s", self._path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def add_slots(self, moments: list[datetime]) -> int:
        added = 0
        for moment in moments:
            cursor = await self.conn.execute(
                "INSERT OR IGNORE INTO slots (starts_at, created_at) VALUES (?, ?)",
                (timeutils.to_iso(moment), timeutils.to_iso(timeutils.now())),
            )
            added += cursor.rowcount
        await self.conn.commit()
        return added

    async def free_slots(self, limit: int = 20) -> list[Slot]:
        cursor = await self.conn.execute(
            "SELECT * FROM slots WHERE is_booked = 0 AND starts_at > ? "
            "ORDER BY starts_at LIMIT ?",
            (timeutils.to_iso(timeutils.now()), limit),
        )
        return [_to_slot(row) for row in await cursor.fetchall()]

    async def upcoming_slots(self, limit: int = 30) -> list[Slot]:
        cursor = await self.conn.execute(
            "SELECT * FROM slots WHERE starts_at > ? ORDER BY starts_at LIMIT ?",
            (timeutils.to_iso(timeutils.now()), limit),
        )
        return [_to_slot(row) for row in await cursor.fetchall()]

    async def get_slot(self, slot_id: int) -> Slot | None:
        cursor = await self.conn.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
        row = await cursor.fetchone()
        return _to_slot(row) if row else None

    async def delete_free_slot(self, slot_id: int) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM slots WHERE id = ? AND is_booked = 0", (slot_id,)
        )
        await self.conn.commit()
        return cursor.rowcount == 1

    async def create_application(
        self,
        *,
        slot_id: int | None,
        user_id: int,
        username: str | None,
        full_name: str,
        address: str,
        phone: str,
        service: str,
    ) -> Application | None:
        try:
            if slot_id is not None:
                cursor = await self.conn.execute(
                    "UPDATE slots SET is_booked = 1 WHERE id = ? AND is_booked = 0",
                    (slot_id,),
                )
                if cursor.rowcount != 1:
                    await self.conn.rollback()
                    return None
            cursor = await self.conn.execute(
                "INSERT INTO applications "
                "(slot_id, user_id, username, full_name, address, phone, service, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    slot_id,
                    user_id,
                    username,
                    full_name,
                    address,
                    phone,
                    service,
                    timeutils.to_iso(timeutils.now()),
                ),
            )
            await self.conn.commit()
        except Exception:
            await self.conn.rollback()
            raise
        return await self.get_application(cursor.lastrowid)

    async def get_application(self, application_id: int) -> Application | None:
        cursor = await self.conn.execute(
            f"SELECT {APPLICATION_FIELDS} FROM applications a "
            "LEFT JOIN slots s ON s.id = a.slot_id WHERE a.id = ?",
            (application_id,),
        )
        row = await cursor.fetchone()
        return _to_application(row) if row else None

    async def pending_reminders(self) -> list[Application]:
        cursor = await self.conn.execute(
            f"SELECT {APPLICATION_FIELDS} FROM applications a "
            "JOIN slots s ON s.id = a.slot_id "
            "WHERE a.reminded = 0 AND s.starts_at > ? ORDER BY s.starts_at",
            (timeutils.to_iso(timeutils.now()),),
        )
        return [_to_application(row) for row in await cursor.fetchall()]

    async def mark_reminded(self, application_id: int) -> None:
        await self.conn.execute(
            "UPDATE applications SET reminded = 1 WHERE id = ?", (application_id,)
        )
        await self.conn.commit()

    async def recent_applications(self, limit: int = 10) -> list[Application]:
        cursor = await self.conn.execute(
            f"SELECT {APPLICATION_FIELDS} FROM applications a "
            "LEFT JOIN slots s ON s.id = a.slot_id "
            "ORDER BY a.id DESC LIMIT ?",
            (limit,),
        )
        return [_to_application(row) for row in await cursor.fetchall()]
