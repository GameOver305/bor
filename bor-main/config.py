"""
إعدادات البوت - Bot Configuration
"""
import os
from typing import Optional
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class Config:
    """إعدادات البوت"""
    
    # Discord Configuration
    BOT_TOKEN: str = os.getenv('DISCORD_BOT_TOKEN', '')
    GUILD_ID: Optional[int] = int(os.getenv('GUILD_ID')) if os.getenv('GUILD_ID') and os.getenv('GUILD_ID').strip() else None
    
    # Owner Configuration
    OWNER_ID: int = int(os.getenv('OWNER_ID', 1376784524016619551))
    
    # Role IDs
    ADMIN_ROLE_ID: int = int(os.getenv('ADMIN_ROLE_ID')) if os.getenv('ADMIN_ROLE_ID') and os.getenv('ADMIN_ROLE_ID').strip() else 0
    MODERATOR_ROLE_ID: int = int(os.getenv('MODERATOR_ROLE_ID')) if os.getenv('MODERATOR_ROLE_ID') and os.getenv('MODERATOR_ROLE_ID').strip() else 0
    
    # Channel IDs
    LOG_CHANNEL_ID: Optional[int] = int(os.getenv('LOG_CHANNEL_ID')) if os.getenv('LOG_CHANNEL_ID') and os.getenv('LOG_CHANNEL_ID').strip() else None
    ANNOUNCEMENT_CHANNEL_ID: Optional[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID')) if os.getenv('ANNOUNCEMENT_CHANNEL_ID') and os.getenv('ANNOUNCEMENT_CHANNEL_ID').strip() else None
    
    # Bot Settings
    MAX_ACTIVE_BOOKINGS: int = int(os.getenv('MAX_ACTIVE_BOOKINGS', 5))
    LANGUAGE: str = os.getenv('LANGUAGE', 'EN').strip().lower()
    TIMEZONE: str = os.getenv('TIMEZONE', 'Asia/Riyadh')
    
    # Reminder Settings
    REMINDER_24H: bool = os.getenv('REMINDER_24H', 'true').lower() == 'true'
    REMINDER_1H: bool = os.getenv('REMINDER_1H', 'true').lower() == 'true'
    REMINDER_NOW: bool = os.getenv('REMINDER_NOW', 'true').lower() == 'true'
    
    # Backup Settings
    AUTO_BACKUP_HOURS: int = int(os.getenv('AUTO_BACKUP_HOURS', 6))
    
    # Paths - Use absolute paths to avoid working directory issues
    _BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH: str = os.path.abspath(os.path.join(_BASE_DIR, 'data', 'bookings.db'))
    BACKUP_DIR: str = os.path.abspath(os.path.join(_BASE_DIR, 'data', 'backups'))
    LOGS_DIR: str = os.path.abspath(os.path.join(_BASE_DIR, 'logs'))
    
    # Booking Types
    BOOKING_TYPES = {
        'building': {'emoji': '🏗️', 'name': 'البناء', 'color': 0x3498db},
        'research': {'emoji': '🔬', 'name': 'الأبحاث', 'color': 0x9b59b6},
        'training': {'emoji': '⚔️', 'name': 'التدريب', 'color': 0xe74c3c}
    }
    
    # Points System
    POINTS_COMPLETED: int = 10
    POINTS_ON_TIME: int = 5
    POINTS_CANCELLED: int = -5
    
    # Achievements
    ACHIEVEMENTS = {
        'perfect_player': {'name': '🥇 لاعب مثالي', 'description': '100+ حجز منجز', 'requirement': 100},
        'fast_builder': {'name': '⚡ سريع البناء', 'description': 'أسرع إنجاز', 'requirement': 1},
        'committed': {'name': '🎯 ملتزم', 'description': 'لم يلغي أي حجز', 'requirement': 1},
        'organized': {'name': '📅 منظم', 'description': 'حجز مسبق دائماً', 'requirement': 10}
    }
    
    @classmethod
    def validate(cls) -> bool:
        """التحقق من صحة الإعدادات"""
        if not cls.BOT_TOKEN:
            print("❌ خطأ: DISCORD_BOT_TOKEN غير موجود في ملف .env")
            return False

        if cls.LANGUAGE not in {'en', 'ar'}:
            print("⚠️ LANGUAGE غير صالح، سيتم استخدام EN")
            cls.LANGUAGE = 'en'
        return True

config = Config()
