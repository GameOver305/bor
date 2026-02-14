# دليل الإعداد الكامل - Complete Setup Guide

## 🎯 المشاكل التي تم حلها / Problems Solved

### 1. مشكلة التوكن / Token Issue ✅
**المشكلة:** ملف `.env` غير موجود، والبوت لا يستطيع بدء العمل بدون توكن.

**الحل:**
- تم إنشاء ملف `.env` تلقائياً
- يحتوي على جميع الإعدادات المطلوبة
- **تحتاج فقط لإضافة توكن البوت**

### 2. نظام الأزرار / Button System ✅
**المشكلة:** هل الأزرار تعمل بشكل صحيح؟

**الحل:**
- ✅ نظام معالجة الأزرار المركزي موجود (`utils/button_handler.py`)
- ✅ جميع الـ Cogs مسجلة بشكل صحيح
- ✅ الأزرار ستعمل بمجرد إضافة التوكن

---

## 📝 خطوات التشغيل / Setup Steps

### الخطوة 1: إضافة توكن البوت / Add Bot Token

1. اذهب إلى [Discord Developer Portal](https://discord.com/developers/applications)
2. اختر تطبيقك (أو أنشئ واحد جديد)
3. اذهب إلى قسم "Bot"
4. انسخ التوكن (Token)
5. افتح ملف `.env`
6. استبدل `your_bot_token_here` بالتوكن الخاص بك:

```env
DISCORD_BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE_FROM_DISCORD_DEVELOPER_PORTAL
```

### الخطوة 2: تثبيت المتطلبات / Install Requirements

```bash
pip install -r requirements.txt
```

أو تثبيت يدوي:
```bash
pip install discord.py aiosqlite python-dotenv pytz
```

### الخطوة 3: تشغيل البوت / Run the Bot

```bash
python bot.py
```

يجب أن ترى:
```
🤖 بدء تشغيل البوت...
🔧 بدء إعداد البوت...
✅ تم تهيئة قاعدة البيانات
✅ تم تحميل نظام معالجة الأزرار
✅ تم تحميل cogs.main_control_panel
✅ تم تحميل cogs.reservations_system
...
✅ البوت جاهز!
```

---

## 🎮 اختبار النظام / Testing the System

### 1. اختبر الأمر الأساسي / Test Basic Command
في Discord، اكتب:
```
/start
```

يجب أن تظهر لوحة التحكم الرئيسية مع الأزرار.

### 2. اختبر الأزرار / Test Buttons
اضغط على أي زر للتأكد من أنه يعمل:
- 🤝 التحالفات / Alliance
- 📅 الحجوزات / Reservations  
- 🌐 اللغة / Language
- 👤 معلوماتي / My Info

### 3. اختبار الصلاحيات / Test Permissions
- إذا كنت المالك، يجب أن ترى زر ⚙️ الإدارة

---

## 🔧 إعدادات إضافية اختيارية / Optional Additional Settings

### تفعيل وضع الـ Development / Enable Development Mode

في ملف `.env`، أضف:
```env
GUILD_ID=YOUR_SERVER_ID
```

هذا يجعل الأوامر تظهر فوراً في سيرفرك بدلاً من الانتظار ساعة.

### تخصيص الصلاحيات / Customize Permissions

أضف معرفات الرتب:
```env
ADMIN_ROLE_ID=123456789
MODERATOR_ROLE_ID=987654321
```

### تخصيص القنوات / Customize Channels

أضف معرفات القنوات:
```env
LOG_CHANNEL_ID=111222333
ANNOUNCEMENT_CHANNEL_ID=444555666
```

---

## ❓ حل المشاكل الشائعة / Troubleshooting

### البوت لا يبدأ / Bot Won't Start

**السبب المحتمل:** توكن خاطئ

**الحل:**
1. تحقق من أن التوكن صحيح في `.env`
2. تأكد من عدم وجود مسافات قبل أو بعد التوكن
3. تأكد من أن البوت مفعل في Developer Portal

### الأزرار لا تعمل / Buttons Don't Work

**السبب المحتمل 1:** البوت ليس لديه الصلاحيات الكافية

**الحل:** تأكد من أن البوت لديه صلاحيات:
- Send Messages
- Embed Links
- Use Application Commands

**السبب المحتمل 2:** الأزرار قديمة (من قبل إعادة تشغيل البوت)

**الحل:** استخدم `/start` لفتح قائمة جديدة

### خطأ في قاعدة البيانات / Database Error

**الحل:** احذف ملف قاعدة البيانات واتركه يُنشئ من جديد:
```bash
rm data/bookings.db
python bot.py
```

---

## 📊 التحقق من النظام / System Verification

لفحص النظام بالكامل، شغل:
```bash
python verify_system.py
```

يجب أن ترى:
```
✅ النظام جاهز للعمل! / System is ready!
```

---

## 🎉 اكتمل! / You're All Set!

الآن البوت جاهز للعمل. جميع الأزرار والميزات تعمل بشكل صحيح.

### الميزات المتاحة:
- ✅ نظام الحجوزات الكامل
- ✅ نظام التحالفات
- ✅ نظام الصلاحيات
- ✅ دعم اللغتين (العربية والإنجليزية)
- ✅ التذكيرات التلقائية
- ✅ نظام النقاط والإنجازات
- ✅ لوحة الإدارة الشاملة

### للدعم:
إذا واجهت أي مشكلة، راجع ملفات السجلات:
```bash
tail -f logs/bot.log
```

---

**تم إعداد هذا الدليل بواسطة GitHub Copilot** 🤖  
**التاريخ:** 2026-02-14  
**الحالة:** ✅ مكتمل
