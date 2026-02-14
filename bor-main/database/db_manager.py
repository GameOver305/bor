"""
مدير قاعدة البيانات - Database Manager
"""
import aiosqlite
import os
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from .models import User, Booking, Alliance, Achievement, Log
from config import config

logger = logging.getLogger('db_manager')


class DatabaseManager:
    """
    مدير قاعدة البيانات - Database Manager
    
    Provides robust database operations with automatic recovery from connection failures.
    """
    
    # Default retry configuration constants
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 0.1  # seconds
    DEFAULT_MAX_DELAY = 2.0    # seconds

    def __init__(self, db_path: str = None, max_retries: int = None, 
                 retry_delay: float = None, max_delay: float = None):
        """
        Initialize database manager with configurable retry behavior.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to config.DATABASE_PATH
            max_retries: Maximum number of retry attempts for database operations (default: 3)
                        This handles transient failures and allows time for recovery
            retry_delay: Initial delay in seconds between retries (default: 0.1)
                        Uses exponential backoff with zero-indexed attempts:
                        - Attempt 0: 0.1s (retry_delay * 2^0)
                        - Attempt 1: 0.2s (retry_delay * 2^1)
                        - Attempt 2: 0.4s (retry_delay * 2^2)
            max_delay: Maximum delay cap in seconds (default: 2.0)
                      Prevents excessive wait times if max_retries is increased
        """
        self.db_path = db_path or config.DATABASE_PATH
        self._initialized = False
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        self.retry_delay = retry_delay if retry_delay is not None else self.DEFAULT_RETRY_DELAY
        self.max_delay = max_delay if max_delay is not None else self.DEFAULT_MAX_DELAY
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists before connecting"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.debug(f"Ensured database directory exists: {db_dir}")
            except Exception as e:
                logger.error(f"Failed to create database directory {db_dir}: {e}")
                raise
    
    def _validate_db_path(self):
        """Validate database path before connection"""
        if not self.db_path:
            raise ValueError("Database path is not configured")
        
        if not os.path.isabs(self.db_path):
            logger.warning(f"Database path is not absolute: {self.db_path}")
        
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            logger.warning(f"Database directory does not exist: {db_dir}")
            self._ensure_db_directory()
    
    async def _ensure_db_initialized(self):
        """Ensure database is initialized, reinitialize if file is missing"""
        db_exists = os.path.exists(self.db_path)
        
        if not db_exists or not self._initialized:
            if not db_exists:
                logger.warning(f"Database file not found at {self.db_path}, initializing...")
            
            try:
                await self.initialize()
                self._initialized = True
                logger.info(f"Database initialized successfully at {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
    
    async def _execute_with_retry(self, operation, operation_name="database operation"):
        """
        Execute a database operation with retry logic.
        
        Uses exponential backoff with a maximum delay cap to handle transient failures
        while preventing excessive wait times.
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Validate and ensure directory exists
                self._validate_db_path()
                self._ensure_db_directory()
                
                # Ensure database is initialized
                await self._ensure_db_initialized()
                
                # Execute the operation
                result = await operation()
                logger.debug(f"{operation_name} succeeded (attempt {attempt + 1})")
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff with maximum delay cap
                    delay = min(self.retry_delay * (2 ** attempt), self.max_delay)
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name} failed after {self.max_retries} attempts: {e}"
                    )
        
        # If all retries failed, raise the last exception
        raise last_exception

    async def initialize(self):
        """تهيئة قاعدة البيانات وتطبيق توافق المخططات"""
        self._validate_db_path()
        self._ensure_db_directory()

        async with aiosqlite.connect(self.db_path) as db:
            # Use absolute path for schema file
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()

            await db.executescript(schema)
            await self._ensure_compatibility(db)
            await db.commit()
        
        self._initialized = True

    async def _ensure_compatibility(self, db: aiosqlite.Connection):
        """توافق الإصدارات القديمة بدون كسر البيانات"""
        users_cols = await self._get_columns(db, 'users')
        alliances_cols = await self._get_columns(db, 'alliances')

        if 'language' not in users_cols:
            await db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'")

        if 'tag' not in alliances_cols:
            await db.execute("ALTER TABLE alliances ADD COLUMN tag TEXT")

        await db.execute("UPDATE users SET language = 'en' WHERE language IS NULL OR TRIM(language) = ''")
        await db.execute("UPDATE users SET language = lower(language)")
        await db.execute("UPDATE users SET language = 'en' WHERE language NOT IN ('ar', 'en')")

        rows = await db.execute_fetchall("SELECT alliance_id, name, tag FROM alliances")
        for alliance_id, name, tag in rows:
            if tag and len(tag.strip()) == 3:
                continue

            seed = ''.join(ch for ch in (name or '').upper() if ch.isalnum())[:3]
            if len(seed) < 3:
                seed = (seed + f"{alliance_id:03d}")[:3]

            candidate = seed
            suffix = 0
            while True:
                exists = await db.execute_fetchone(
                    "SELECT 1 FROM alliances WHERE tag = ? AND alliance_id != ?",
                    (candidate, alliance_id)
                )
                if not exists:
                    break
                suffix += 1
                candidate = f"{seed[:2]}{suffix % 10}"

            await db.execute("UPDATE alliances SET tag = ? WHERE alliance_id = ?", (candidate, alliance_id))

        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_alliances_tag ON alliances(tag)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_users_language ON users(language)")

    async def _get_columns(self, db: aiosqlite.Connection, table: str) -> List[str]:
        rows = await db.execute_fetchall(f"PRAGMA table_info({table})")
        return [r[1] for r in rows]

    def _parse_dt(self, value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
        return None

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """تنفيذ استعلام"""
        async def _do_execute():
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                await db.commit()
                return cursor
        
        return await self._execute_with_retry(_do_execute, "execute query")

    async def fetchone(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """جلب صف واحد"""
        async def _do_fetchone():
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                return await cursor.fetchone()
        
        return await self._execute_with_retry(_do_fetchone, "fetchone query")

    async def fetchall(self, query: str, params: tuple = ()) -> List[tuple]:
        """جلب كل الصفوف"""
        async def _do_fetchall():
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                return await cursor.fetchall()
        
        return await self._execute_with_retry(_do_fetchall, "fetchall query")

    async def _fetchone_row(self, query: str, params: tuple = ()):
        async def _do_fetchone_row():
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                return await cursor.fetchone()
        
        return await self._execute_with_retry(_do_fetchone_row, "fetchone_row query")

    async def _fetchall_rows(self, query: str, params: tuple = ()):
        async def _do_fetchall_rows():
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                return await cursor.fetchall()
        
        return await self._execute_with_retry(_do_fetchall_rows, "fetchall_rows query")

    def _row_to_user(self, row) -> Optional[User]:
        if not row:
            return None
        return User(
            user_id=row['user_id'],
            discord_id=row['discord_id'],
            username=row['username'],
            player_id=row['player_id'],
            alliance_id=row['alliance_id'],
            alliance_rank=row['alliance_rank'] or 'R1',
            points=row['points'] or 0,
            total_bookings=row['total_bookings'] or 0,
            completed_bookings=row['completed_bookings'] or 0,
            cancelled_bookings=row['cancelled_bookings'] or 0,
            language=(row['language'] or 'en').lower(),
            last_activity=self._parse_dt(row['last_activity']),
            created_at=self._parse_dt(row['created_at']),
            updated_at=self._parse_dt(row['updated_at'])
        )

    def _row_to_booking(self, row) -> Optional[Booking]:
        if not row:
            return None
        return Booking(
            booking_id=row['booking_id'],
            user_id=row['user_id'],
            booking_type=row['booking_type'],
            player_name=row['player_name'],
            player_id=row['player_id'],
            alliance_name=row['alliance_name'],
            scheduled_time=self._parse_dt(row['scheduled_time']),
            details=row['details'] or '',
            status=row['status'] or 'active',
            reminder_24h_sent=bool(row['reminder_24h_sent']),
            reminder_1h_sent=bool(row['reminder_1h_sent']),
            reminder_now_sent=bool(row['reminder_now_sent']),
            completed_at=self._parse_dt(row['completed_at']),
            cancelled_at=self._parse_dt(row['cancelled_at']),
            cancellation_reason=row['cancellation_reason'],
            created_at=self._parse_dt(row['created_at']),
            updated_at=self._parse_dt(row['updated_at']),
            created_by=row['created_by'] or '',
            duration_days=row['duration_days'] or 1
        )

    def _row_to_alliance(self, row) -> Optional[Alliance]:
        if not row:
            return None
        return Alliance(
            alliance_id=row['alliance_id'],
            name=row['name'],
            tag=(row['tag'] or '').upper(),
            description=row['description'] or '',
            rules=row['rules'] or '',
            leader_id=row['leader_id'],
            level=row['level'] or 1,
            total_power=row['total_power'] or 0,
            member_count=row['member_count'] or 1,
            max_members=row['max_members'] or 50,
            location=row['location'] or '',
            total_bookings=row['total_bookings'] or 0,
            total_points=row['total_points'] or 0,
            created_at=self._parse_dt(row['created_at'])
        )

    # ====== User Methods ======

    async def get_or_create_user(self, discord_id: str, username: str, player_id: str) -> User:
        user = await self.get_user_by_discord_id(discord_id)
        if user:
            return user

        await self.execute(
            """INSERT INTO users (discord_id, username, player_id, language)
               VALUES (?, ?, ?, ?)""",
            (discord_id, username, player_id or discord_id, config.LANGUAGE)
        )
        return await self.get_user_by_discord_id(discord_id)

    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        row = await self._fetchone_row(
            "SELECT * FROM users WHERE discord_id = ?",
            (discord_id,)
        )
        return self._row_to_user(row)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        row = await self._fetchone_row("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self._row_to_user(row)

    async def set_user_language(self, discord_id: str, language: str):
        lang = (language or 'en').lower()
        if lang not in ('ar', 'en'):
            lang = 'en'
        await self.execute(
            "UPDATE users SET language = ?, updated_at = CURRENT_TIMESTAMP WHERE discord_id = ?",
            (lang, discord_id)
        )

    async def update_user_points(self, user_id: int, points_delta: int):
        await self.execute(
            "UPDATE users SET points = points + ?, updated_at = ? WHERE user_id = ?",
            (points_delta, datetime.now().isoformat(), user_id)
        )

    async def update_user_stats(self, user_id: int, stat_type: str):
        if stat_type == 'completed':
            await self.execute(
                """UPDATE users SET completed_bookings = completed_bookings + 1,
                   total_bookings = total_bookings + 1, updated_at = ? WHERE user_id = ?""",
                (datetime.now().isoformat(), user_id)
            )
        elif stat_type == 'cancelled':
            await self.execute(
                """UPDATE users SET cancelled_bookings = cancelled_bookings + 1,
                   updated_at = ? WHERE user_id = ?""",
                (datetime.now().isoformat(), user_id)
            )

    # ====== Booking Methods ======

    async def create_booking(self, booking: Booking) -> int:
        async def _do_create_booking():
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """INSERT INTO bookings
                       (user_id, booking_type, player_name, player_id, alliance_name,
                        scheduled_time, details, created_by, duration_days)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        booking.user_id,
                        booking.booking_type,
                        booking.player_name,
                        booking.player_id,
                        booking.alliance_name,
                        booking.scheduled_time.isoformat() if isinstance(booking.scheduled_time, datetime) else booking.scheduled_time,
                        booking.details,
                        booking.created_by,
                        booking.duration_days,
                    )
                )
                await db.commit()
                return cursor.lastrowid
        
        return await self._execute_with_retry(_do_create_booking, "create booking")

    async def get_booking(self, booking_id: int) -> Optional[Booking]:
        row = await self._fetchone_row("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        return self._row_to_booking(row)

    async def get_user_bookings(self, user_id: int, status: str = None) -> List[Booking]:
        if status:
            rows = await self._fetchall_rows(
                "SELECT * FROM bookings WHERE user_id = ? AND status = ? ORDER BY scheduled_time ASC",
                (user_id, status)
            )
        else:
            rows = await self._fetchall_rows(
                "SELECT * FROM bookings WHERE user_id = ? ORDER BY scheduled_time ASC",
                (user_id,)
            )
        return [self._row_to_booking(row) for row in rows]

    async def get_bookings_by_type(self, booking_type: str, status: str = 'active') -> List[Booking]:
        rows = await self._fetchall_rows(
            "SELECT * FROM bookings WHERE booking_type = ? AND status = ? ORDER BY scheduled_time ASC",
            (booking_type, status)
        )
        return [self._row_to_booking(row) for row in rows]

    async def get_all_active_bookings(self) -> List[Booking]:
        rows = await self._fetchall_rows(
            "SELECT * FROM bookings WHERE status = 'active' ORDER BY scheduled_time ASC"
        )
        return [self._row_to_booking(row) for row in rows]

    async def update_booking_status(self, booking_id: int, status: str):
        await self.execute(
            "UPDATE bookings SET status = ?, updated_at = ? WHERE booking_id = ?",
            (status, datetime.now().isoformat(), booking_id)
        )

    async def cancel_booking(self, booking_id: int, reason: str = None):
        now = datetime.now().isoformat()
        await self.execute(
            """UPDATE bookings SET status = 'cancelled', cancelled_at = ?,
               cancellation_reason = ?, updated_at = ? WHERE booking_id = ?""",
            (now, reason, now, booking_id)
        )

    async def complete_booking(self, booking_id: int):
        now = datetime.now().isoformat()
        await self.execute(
            """UPDATE bookings SET status = 'completed', completed_at = ?,
               updated_at = ? WHERE booking_id = ?""",
            (now, now, booking_id)
        )

    async def update_reminder_sent(self, booking_id: int, reminder_type: str):
        field_map = {'24h': 'reminder_24h_sent', '1h': 'reminder_1h_sent', 'now': 'reminder_now_sent'}
        field = field_map.get(reminder_type)
        if field:
            await self.execute(f"UPDATE bookings SET {field} = 1 WHERE booking_id = ?", (booking_id,))

    async def check_booking_conflict(self, user_id: int, scheduled_time: datetime) -> bool:
        value = scheduled_time.isoformat() if isinstance(scheduled_time, datetime) else scheduled_time
        result = await self.fetchone(
            """SELECT COUNT(*) FROM bookings
               WHERE user_id = ? AND status = 'active' AND scheduled_time = ?""",
            (user_id, value)
        )
        return result[0] > 0 if result else False

    async def get_active_bookings_count(self, user_id: int) -> int:
        result = await self.fetchone(
            "SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status = 'active'",
            (user_id,)
        )
        return result[0] if result else 0

    # ====== Alliance Methods ======

    async def create_alliance(self, name: str, tag: str, leader_id: int | str, description: str = '') -> int:
        clean_tag = (tag or '').strip().upper()
        if len(clean_tag) != 3:
            raise ValueError('Alliance tag must be exactly 3 characters')

        if isinstance(leader_id, str):
            leader_user = await self.get_user_by_discord_id(leader_id)
            if not leader_user:
                raise ValueError('Leader user not found in database')
            leader_db_id = leader_user.user_id
        else:
            leader_db_id = leader_id

        async def _do_create_alliance():
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "INSERT INTO alliances (name, tag, leader_id, description, member_count) VALUES (?, ?, ?, ?, 1)",
                    (name, clean_tag, leader_db_id, description)
                )
                alliance_id = cursor.lastrowid

                await db.execute(
                    "UPDATE users SET alliance_id = ?, alliance_rank = 'R5', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (alliance_id, leader_db_id)
                )
                await db.commit()
                return alliance_id
        
        return await self._execute_with_retry(_do_create_alliance, "create alliance")

    async def get_alliance(self, alliance_id: int) -> Optional[Alliance]:
        row = await self._fetchone_row("SELECT * FROM alliances WHERE alliance_id = ?", (alliance_id,))
        return self._row_to_alliance(row)

    async def get_alliance_by_name(self, name: str) -> Optional[Alliance]:
        row = await self._fetchone_row("SELECT * FROM alliances WHERE name = ?", (name,))
        return self._row_to_alliance(row)

    async def get_alliance_by_tag(self, tag: str) -> Optional[Alliance]:
        row = await self._fetchone_row("SELECT * FROM alliances WHERE tag = ?", ((tag or '').upper(),))
        return self._row_to_alliance(row)

    async def join_alliance(self, user_id: int, alliance_id: int):
        await self.execute(
            "UPDATE users SET alliance_id = ?, alliance_rank = 'R1', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (alliance_id, user_id)
        )
        await self.execute(
            "UPDATE alliances SET member_count = member_count + 1 WHERE alliance_id = ?",
            (alliance_id,)
        )

    async def leave_alliance(self, user_id: int, alliance_id: int):
        await self.execute(
            "UPDATE users SET alliance_id = NULL, alliance_rank = 'R1', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        await self.execute(
            "UPDATE alliances SET member_count = CASE WHEN member_count > 0 THEN member_count - 1 ELSE 0 END WHERE alliance_id = ?",
            (alliance_id,)
        )

    # ====== Achievement Methods ======

    async def award_achievement(self, user_id: int, achievement_type: str, achievement_name: str) -> bool:
        try:
            await self.execute(
                "INSERT INTO achievements (user_id, achievement_type, achievement_name) VALUES (?, ?, ?)",
                (user_id, achievement_type, achievement_name)
            )
            return True
        except Exception:
            return False

    async def get_user_achievements(self, user_id: int) -> List[Achievement]:
        data = await self.fetchall(
            "SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC",
            (user_id,)
        )
        return [Achievement(*row) for row in data]

    # ====== Log Methods ======

    async def log_action(self, action_type: str, description: str, user_id: str = None,
                        booking_id: int = None, details: str = None):
        await self.execute(
            """INSERT INTO logs (action_type, user_id, booking_id, description, details)
               VALUES (?, ?, ?, ?, ?)""",
            (action_type, user_id, booking_id, description, details)
        )

    async def get_logs(self, limit: int = 100) -> List[Log]:
        data = await self.fetchall(
            "SELECT * FROM logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [Log(*row) for row in data]

    # ====== Statistics Methods ======

    async def get_stats(self) -> Dict[str, Any]:
        total_bookings = await self.fetchone("SELECT COUNT(*) FROM bookings")
        active_bookings = await self.fetchone("SELECT COUNT(*) FROM bookings WHERE status = 'active'")
        completed_bookings = await self.fetchone("SELECT COUNT(*) FROM bookings WHERE status = 'completed'")
        total_users = await self.fetchone("SELECT COUNT(*) FROM users")
        total_alliances = await self.fetchone("SELECT COUNT(*) FROM alliances")

        return {
            'total_bookings': total_bookings[0] if total_bookings else 0,
            'active_bookings': active_bookings[0] if active_bookings else 0,
            'completed_bookings': completed_bookings[0] if completed_bookings else 0,
            'total_users': total_users[0] if total_users else 0,
            'total_alliances': total_alliances[0] if total_alliances else 0
        }

    async def get_leaderboard(self, limit: int = 10) -> List[User]:
        rows = await self._fetchall_rows(
            "SELECT * FROM users ORDER BY points DESC, completed_bookings DESC LIMIT ?",
            (limit,)
        )
        return [self._row_to_user(row) for row in rows]

    async def get_top_alliances(self, limit: int = 10) -> List[Alliance]:
        rows = await self._fetchall_rows(
            "SELECT * FROM alliances ORDER BY total_points DESC, total_bookings DESC LIMIT ?",
            (limit,)
        )
        return [self._row_to_alliance(row) for row in rows]


# Instance global
db = DatabaseManager()
