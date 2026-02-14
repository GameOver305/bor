#!/usr/bin/env python3
"""
التحقق الشامل من نظام البوت - Comprehensive Bot System Verification
يفحص التوكن، الأزرار، الإعدادات، والتكامل
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("فحص شامل لنظام البوت / Comprehensive Bot System Verification")
print("=" * 70)

# 1. Check .env file
print("\n📋 1. فحص ملف .env / Checking .env file")
print("-" * 70)
env_file = Path('.env')
if env_file.exists():
    print("✅ ملف .env موجود / .env file exists")
    with open('.env', 'r') as f:
        lines = f.readlines()
        has_token = any('DISCORD_BOT_TOKEN' in line and not line.strip().startswith('#') for line in lines)
        token_value = None
        for line in lines:
            if 'DISCORD_BOT_TOKEN' in line and not line.strip().startswith('#'):
                token_value = line.split('=', 1)[1].strip() if '=' in line else None
        
        if has_token and token_value and token_value not in ['', 'your_bot_token_here']:
            print(f"✅ التوكن موجود / Token exists (length: {len(token_value)} chars)")
        else:
            print("❌ التوكن غير موجود أو فارغ / Token missing or empty")
            print("⚠️ حل: أضف توكن البوت في ملف .env")
else:
    print("❌ ملف .env غير موجود / .env file not found")
    print("⚠️ حل: انسخ .env.example إلى .env وأضف التوكن")

# 2. Check configuration loading
print("\n📋 2. فحص تحميل الإعدادات / Checking configuration loading")
print("-" * 70)
try:
    from config import config
    print("✅ تم تحميل config بنجاح / Config loaded successfully")
    
    # Check critical settings
    if config.BOT_TOKEN:
        print(f"✅ BOT_TOKEN: موجود (طول: {len(config.BOT_TOKEN)} حرف)")
    else:
        print("❌ BOT_TOKEN: فارغ / Empty")
    
    print(f"✅ DATABASE_PATH: {config.DATABASE_PATH}")
    print(f"✅ LANGUAGE: {config.LANGUAGE}")
    
except Exception as e:
    print(f"❌ فشل تحميل config: {e}")

# 3. Check button handler system
print("\n📋 3. فحص نظام معالجة الأزرار / Checking button handler system")
print("-" * 70)
try:
    from utils.button_handler import button_handler, ButtonHandlerCog
    print("✅ تم تحميل button_handler بنجاح / Button handler loaded successfully")
    
    # Check registered handlers
    handlers = button_handler.get_registered_handlers()
    direct = handlers.get('direct_handlers', [])
    prefix = handlers.get('prefix_handlers', [])
    
    print(f"✅ معالجات مباشرة / Direct handlers: {len(direct)}")
    if direct:
        for h in direct[:5]:
            print(f"   - {h}")
    
    print(f"✅ معالجات البادئات / Prefix handlers: {len(prefix)}")
    if prefix:
        for p in prefix:
            print(f"   - {p}*")
    
    if len(prefix) == 0:
        print("⚠️ لم يتم تسجيل أي معالجات بادئة بعد / No prefix handlers registered yet")
        print("   (سيتم تسجيلها عند تحميل الـ Cogs / Will be registered when cogs load)")
    
except Exception as e:
    print(f"❌ فشل تحميل button_handler: {e}")

# 4. Check button views
print("\n📋 4. فحص الـ Views والأزرار / Checking Views and Buttons")
print("-" * 70)
try:
    from utils.buttons import MainMenuView, BookingTypeSelectView, AllianceMenuView
    print("✅ تم تحميل Views بنجاح / Views loaded successfully")
    
    # Check MainMenuView
    main_view = MainMenuView()
    print(f"✅ MainMenuView: {len(main_view.children)} أزرار / buttons")
    for child in main_view.children[:5]:
        if hasattr(child, 'custom_id'):
            print(f"   - {child.custom_id}")
    
    # Check BookingTypeSelectView
    booking_view = BookingTypeSelectView()
    print(f"✅ BookingTypeSelectView: {len(booking_view.children)} أزرار / buttons")
    
except Exception as e:
    print(f"❌ فشل تحميل Views: {e}")

# 5. Check all cogs
print("\n📋 5. فحص الـ Cogs / Checking Cogs")
print("-" * 70)
cogs_to_check = [
    'cogs.main_control_panel',
    'cogs.reservations_system',
    'cogs.alliance_system',
    'cogs.management_system',
    'cogs.help_system',
]

for cog_name in cogs_to_check:
    try:
        module = __import__(cog_name, fromlist=[''])
        print(f"✅ {cog_name}: يمكن تحميله / Can be imported")
    except Exception as e:
        print(f"❌ {cog_name}: فشل التحميل / Failed: {e}")

# 6. Check database
print("\n📋 6. فحص قاعدة البيانات / Checking Database")
print("-" * 70)
async def check_database():
    try:
        from database import db
        print("✅ تم تحميل database module بنجاح / Database module loaded")
        
        # Check if database file exists
        if os.path.exists(config.DATABASE_PATH):
            size = os.path.getsize(config.DATABASE_PATH)
            print(f"✅ ملف قاعدة البيانات موجود / Database file exists ({size} bytes)")
        else:
            print(f"⚠️ ملف قاعدة البيانات غير موجود / Database file not found")
            print(f"   سيتم إنشاؤه عند تشغيل البوت / Will be created when bot starts")
        
        # Try to initialize (without running bot)
        await db.initialize()
        print("✅ تم تهيئة قاعدة البيانات بنجاح / Database initialized successfully")
        
        # Test a simple query
        stats = await db.get_stats()
        print(f"✅ استعلام تجريبي نجح / Test query succeeded: {stats['total_users']} users")
        
    except Exception as e:
        print(f"❌ فشل فحص قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()

# Run async check
asyncio.run(check_database())

# 7. Check dependencies
print("\n📋 7. فحص المكتبات المطلوبة / Checking Dependencies")
print("-" * 70)
required_packages = [
    'discord',
    'aiosqlite',
    'dotenv',
    'pytz',
]

for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package}: مثبت / Installed")
    except ImportError:
        print(f"❌ {package}: غير مثبت / Not installed")
        print(f"   حل: pip install {package}")

# 8. Summary
print("\n" + "=" * 70)
print("📊 الملخص / Summary")
print("=" * 70)

issues_found = []
recommendations = []

if not env_file.exists():
    issues_found.append("ملف .env غير موجود")
    recommendations.append("انسخ .env.example إلى .env: cp .env.example .env")

if not config.BOT_TOKEN or config.BOT_TOKEN == '':
    issues_found.append("التوكن غير موجود في .env")
    recommendations.append("أضف توكن البوت في ملف .env في سطر DISCORD_BOT_TOKEN")

if len(issues_found) == 0:
    print("✅ النظام جاهز للعمل! / System is ready!")
    print("\nلتشغيل البوت / To run the bot:")
    print("  python bot.py")
else:
    print(f"⚠️ تم العثور على {len(issues_found)} مشكلة / Found {len(issues_found)} issue(s):")
    for i, issue in enumerate(issues_found, 1):
        print(f"  {i}. {issue}")
    
    if recommendations:
        print("\n💡 التوصيات / Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

print("\n" + "=" * 70)
print("✅ اكتمل الفحص / Verification Complete")
print("=" * 70)
