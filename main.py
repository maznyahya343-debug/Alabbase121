from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message,
    CallbackQuery,
    ForceReply,
    InlineKeyboardMarkup as Markup,
    InlineKeyboardButton as Button
)
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    UserNotParticipant,
    ChatWriteForbidden,
    PeerIdInvalid,
    FloodWait
)
import os
os.system("pip install pyro-listener")
from pyrolistener import Listener, exceptions
from asyncio import create_task, sleep, get_event_loop, gather
from datetime import datetime, timedelta
from pytz import timezone
from typing import Union, List, Dict, Any, Optional
import json, random, re, asyncio

# =================== إعدادات البوت ===================
app = Client(
    "autoPost",
    api_id="34923196",
    api_hash="b3f6e47ecd3231186f8f7e01ab41938e",
    bot_token='8832559640:AAGGV15XucCuMgQ20StPFGPv8LYANTnb0bc'
)
loop = get_event_loop()
listener = Listener(client=app)
owner = 8310839908

# =================== المتغيرات العامة ===================
active_tasks = set()
failed_groups = set()
privacy_protection_active = True
user_conversations = {}  # تتبع المحادثات الخاصة

# =================== رسائل الترحيب والردود ===================
WELCOME_MESSAGES = [
    "أهلاً بك! نسعد بخدمتك. إذا كان لديك أي استفسار، يسعدنا تواصلك معنا مباشرة عبر واتساب من خلال الرابط التالي: https://wa.me/966575996163",
    "هل لديك أي استفسار؟ نحن هنا لمساعدتك! تفضل بمراسلتنا عبر واتساب بضغطة زر واحدة من خلال الرابط التالي: https://wa.me/966575996163",
    "مرحباً! فريق الدعم جاهز لخدمتك. للتواصل السريع عبر واتساب: https://wa.me/966575996163",
    "أهلاً وسهلاً! إذا كنت بحاجة لأي مساعدة، تواصل معنا عبر واتساب: https://wa.me/966575996163"
]

GREETING_RESPONSES = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته",
    "سلام عليكم": "وعليكم السلام ورحمة الله وبركاته",
    "سلام": "وعليكم السلام",
    "هلا": "هلا بك",
    "مرحبا": "مرحباً بك",
    "اهلا": "أهلاً بك",
    "هاي": "هاي",
    "hello": "Hello! Welcome",
    "hi": "Hi there! Welcome",
    "hey": "Hey! Welcome"
}

# =================== دوال مساعدة ===================
def get_home_markup(user_id: int) -> Markup:
    """إنشاء أزرار الصفحة الرئيسية"""
    user_data = users.get(str(user_id), {})
    delay_mode_text = "✅ تأخير ذكي مفعل" if user_data.get("smart_delay", True) else "❌ تأخير ذكي معطل"
    delete_mode_text = f"🗑️ حذف: {user_data.get('delete_after', 0)}ث" if user_data.get('delete_after', 0) > 0 else "🗑️ حذف: معطل"
    
    return Markup([
        [Button("- حسابك -", callback_data="account")],
        [Button("- السوبرات -", callback_data="currentSupers"), Button("➕ إضافة", callback_data="newSuper")],
        [Button("- المدة بين النشر -", callback_data="waitTime"), Button("- الكليشات -", callback_data="manageCaptions")],
        [Button("- طريقة التوزيع -", callback_data="distributionMethod")],
        [Button(delete_mode_text, callback_data="deleteTime")],
        [Button("⏹️ إيقاف", callback_data="stopPosting"), Button("▶️ بدء", callback_data="startPosting")],
        [Button(delay_mode_text, callback_data="toggleSmartDelay")],
        [Button("💬 الردود التلقائية", callback_data="autoReplies")],
        [Button("📝 تخصيص الرسائل", callback_data="customMessages")]
    ])

def get_distribution_markup(user_id: int) -> Markup:
    """إنشاء أزرار طرق التوزيع الزمني"""
    current = users[str(user_id)].get("distribution_method", "random")
    methods = {
        "equal": "📏 متساوي",
        "random": "🎲 عشوائي", 
        "fibonacci": "📈 فيبوناتشي"
    }
    markup = []
    for key, name in methods.items():
        status = "✅ " if current == key else "❌ "
        markup.append([Button(f"{status}{name}", callback_data=f"setDist_{key}")])
    markup.append([Button("- الرئيسيه -", callback_data="toHome")])
    return Markup(markup)

def get_auto_replies_markup(user_id: int) -> Markup:
    """إنشاء أزرار إدارة الردود التلقائية"""
    user_data = users.get(str(user_id), {})
    auto_reply_status = user_data.get("auto_reply_enabled", True)
    
    markup = [
        [Button("✅ تفعيل" if auto_reply_status else "❌ تعطيل", callback_data="toggleAutoReply")],
        [Button("📝 إضافة رد جديد", callback_data="addReply")],
        [Button("📋 عرض الردود", callback_data="viewReplies")],
        [Button("🗑️ حذف رد", callback_data="deleteReply")],
        [Button("- الرئيسيه -", callback_data="toHome")]
    ]
    return Markup(markup)

def get_custom_messages_markup(user_id: int) -> Markup:
    """إنشاء أزرار تخصيص الرسائل"""
    return Markup([
        [Button("✏️ تغيير رسالة الترحيب", callback_data="changeWelcome")],
        [Button("✏️ تغيير رسالة التحفيز", callback_data="changeMotivation")],
        [Button("📋 عرض الرسائل الحالية", callback_data="viewCustomMessages")],
        [Button("🔄 استعادة الافتراضي", callback_data="resetMessages")],
        [Button("- الرئيسيه -", callback_data="toHome")]
    ])

def calculate_distributed_delays(num_groups: int, total_time: int, method: str = "random") -> List[float]:
    """حساب الفروق الزمنية بين المجموعات حسب الطريقة المختارة"""
    if num_groups <= 1:
        return [0]
    
    if method == "equal":
        delay_per_group = total_time / num_groups
        return [delay_per_group] * num_groups
    
    elif method == "fibonacci":
        fib = [1, 1]
        for i in range(num_groups - 2):
            fib.append(fib[-1] + fib[-2])
        total_fib = sum(fib[:num_groups])
        return [(total_time * f / total_fib) for f in fib[:num_groups]]
    
    else:  # random
        delays = []
        remaining = total_time
        for i in range(num_groups - 1):
            max_delay = min(remaining - (num_groups - i - 1), remaining * 0.8)
            min_delay = max(1, remaining * 0.1)
            delay = random.uniform(min_delay, max_delay)
            delays.append(delay)
            remaining -= delay
        delays.append(remaining)
        random.shuffle(delays)
        return delays

def get_greeting_response(text: str) -> Optional[str]:
    """الحصول على رد مناسب للتحية"""
    text_lower = text.lower().strip()
    
    # التحقق من التحية المطابقة
    for greeting, response in GREETING_RESPONSES.items():
        if greeting.lower() in text_lower:
            return response
    
    # التحقق من كلمات تحية عامة
    greeting_words = ["سلام", "هلا", "مرحب", "اهلا", "هاي", "hello", "hi", "hey"]
    for word in greeting_words:
        if word in text_lower:
            return GREETING_RESPONSES.get(word.capitalize(), "وعليكم السلام")
    
    return None

# =================== حماية سياسة الخصوصية ===================
PRIVACY_RESPONSES = [
    "اسمي {name} من {country} عمري {age} سنة",
    "أنا {name} من {country}، عمري {age} سنة",
    "الاسم: {name}\nالعمر: {age}\nالبلد: {country}",
    "{name}\n{age} سنة\n{country}",
    "مرحباً، أنا {name}، {age} عام، من {country}",
    "أنا {name} - {age} سنة - من {country}"
]

COUNTRIES = ["مصر", "السعودية", "الإمارات", "الكويت", "قطر", "عمان", "البحرين", "الأردن", "العراق", "سوريا", "لبنان", "فلسطين", "اليمن", "ليبيا", "تونس", "الجزائر", "المغرب", "السودان"]
NAMES = ["أحمد", "محمد", "علي", "حسن", "حسين", "عمر", "عثمان", "خالد", "يوسف", "إبراهيم", "محمود", "مصطفى", "كريم", "سعيد", "نبيل"]
AGES = list(range(18, 65))

async def handle_privacy_bot(client: Client, message: Message, user_id: int) -> bool:
    """معالجة رسائل بوت سياسة الخصوصية بشكل ذكي"""
    global privacy_protection_active
    
    if not privacy_protection_active:
        return False
    
    if not message.text:
        return False
        
    text = message.text.lower()
    
    privacy_keywords = [
        "tell me about yourself", "introduce yourself", "who are you",
        "what is your name", "how old are you", "where are you from",
        "your name", "your age", "your country", "tell us about you",
        "give me information", "personal information", "about you",
        "عرف نفسك", "من انت", "ما اسمك", "كم عمرك", "من اين انت",
        "اعرف عنك", "معلومات عنك", "الاسم", "العمر", "البلد"
    ]
    
    if any(kw in text for kw in privacy_keywords):
        await sleep(random.uniform(3, 8))
        
        response = random.choice(PRIVACY_RESPONSES).format(
            name=random.choice(NAMES),
            age=random.choice(AGES),
            country=random.choice(COUNTRIES)
        )
        
        try:
            await client.send_message(message.chat.id, response)
            return True
        except:
            pass
    
    return False

# =================== معالجة الرسائل الخاصة ===================
@app.on_message(filters.private & filters.text)
async def handle_private_messages(client: Client, message: Message):
    """معالجة جميع الرسائل الخاصة"""
    user_id = message.from_user.id
    text = message.text
    
    # تجاهل الأوامر
    if text.startswith('/'):
        return
    
    # تجاهل رسائل البوت نفسه
    if user_id == app.bot.id:
        return
    
    # التحقق من الإشتراك
    subscribed = await subscription(message)
    if isinstance(subscribed, str):
        return await message.reply(f"⚠️ عليك الإشتراك بقناة البوت أولاً\n📢 القناة: @{subscribed}\nاشترك ثم ارسل /start")
    
    # التحقق من الردود التلقائية للمستخدم
    user_data = users.get(str(user_id), {})
    if not user_data.get("auto_reply_enabled", True):
        return
    
    # معالجة التحية
    greeting_response = get_greeting_response(text)
    if greeting_response:
        # إرسال رد التحية
        await message.reply(greeting_response)
        
        # انتظار قصير ثم إرسال رسالة ترحيبية عشوائية
        await sleep(random.uniform(1, 3))
        
        # الحصول على رسائل مخصصة أو الافتراضية
        custom_welcome = user_data.get("custom_welcome", None)
        custom_motivation = user_data.get("custom_motivation", None)
        
        # اختيار رسالة عشوائية من المتاحة
        available_messages = []
        if custom_welcome:
            available_messages.append(custom_welcome)
        if custom_motivation:
            available_messages.append(custom_motivation)
        if not available_messages:
            available_messages = WELCOME_MESSAGES
        
        welcome_message = random.choice(available_messages)
        
        # إضافة أزرار واتساب
        markup = Markup([
            [Button("📱 تواصل عبر واتساب", url="https://wa.me/966575996163")],
            [Button("💬 المزيد من الخدمات", callback_data="moreServices")]
        ])
        
        await message.reply(welcome_message, reply_markup=markup)
        return
    
    # معالجة الأسئلة الشائعة
    if "?" in text or "؟" in text:
        # رد تلقائي للأسئلة
        await message.reply(
            "📌 لديك سؤال؟ فريق الدعم جاهز لمساعدتك!\n\n"
            "للتواصل السريع عبر واتساب: https://wa.me/966575996163",
            reply_markup=Markup([
                [Button("📱 تواصل عبر واتساب", url="https://wa.me/966575996163")]
            ])
        )
        return

# =================== أزرار الخدمات الإضافية ===================
@app.on_callback_query(filters.regex(r"^(moreServices)$"))
async def more_services(_: Client, callback: CallbackQuery):
    await callback.message.edit_text(
        "🌟 **خدماتنا المميزة:**\n\n"
        "📱 **واتساب:** للتواصل المباشر مع فريق الدعم\n"
        "💬 **تيليجرام:** للاستفسارات السريعة\n"
        "📧 **البريد الإلكتروني:** للتواصل الرسمي\n\n"
        "اختر طريقة التواصل المناسبة لك:",
        reply_markup=Markup([
            [Button("📱 واتساب", url="https://wa.me/966575996163")],
            [Button("💬 التيليجرام", callback_data="telegramContact")],
            [Button("- الرئيسيه -", callback_data="toHome")]
        ])
    )

@app.on_callback_query(filters.regex(r"^(telegramContact)$"))
async def telegram_contact(_: Client, callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 **للتواصل عبر التيليجرام:**\n\n"
        "يمكنك مراسلة المطور مباشرة:\n"
        f"👤 @{app.get_me().username}\n\n"
        "أو عبر البوت مباشرة.",
        reply_markup=Markup([
            [Button("👤 مراسلة المطور", url=f"tg://openmessage?user_id={owner}")],
            [Button("- العوده -", callback_data="moreServices")]
        ])
    )

# =================== إدارة الردود التلقائية ===================
@app.on_callback_query(filters.regex(r"^(autoReplies)$"))
async def auto_replies_menu(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "💬 **إدارة الردود التلقائية**\n\n"
        "قم بتخصيص كيفية رد البوت على الرسائل الخاصة:",
        reply_markup=get_auto_replies_markup(user_id)
    )

@app.on_callback_query(filters.regex(r"^(toggleAutoReply)$"))
async def toggle_auto_reply(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.get(str(user_id), {})
    current = user_data.get("auto_reply_enabled", True)
    users[str(user_id)]["auto_reply_enabled"] = not current
    write(users_db, users)
    
    status = "مفعلة ✅" if not current else "معطلة ❌"
    await callback.answer(f"الردود التلقائية {status}", show_alert=True)
    await auto_replies_menu(_, callback)

@app.on_callback_query(filters.regex(r"^(addReply)$"))
async def add_reply(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        keyword = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="🔑 **أرسل الكلمة المفتاحية**\nمثال: مرحبا\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]]))
    
    if keyword.text == "/cancel":
        return await keyword.reply("✅ تم الإلغاء")
    
    try:
        response = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="💬 **أرسل الرد المناسب**\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]]))
    
    if response.text == "/cancel":
        return await response.reply("✅ تم الإلغاء")
    
    # حفظ الرد
    if "custom_replies" not in users[str(user_id)]:
        users[str(user_id)]["custom_replies"] = {}
    
    users[str(user_id)]["custom_replies"][keyword.text.strip()] = response.text
    write(users_db, users)
    
    await response.reply(f"✅ تم إضافة الرد\n🔑 الكلمة: {keyword.text}\n💬 الرد: {response.text[:50]}...",
                        reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]]))

@app.on_callback_query(filters.regex(r"^(viewReplies)$"))
async def view_replies(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    replies = users.get(str(user_id), {}).get("custom_replies", {})
    
    if not replies:
        return await callback.answer("📭 لا توجد ردود مخصصة", show_alert=True)
    
    text = "📋 **الردود المخصصة:**\n\n"
    for keyword, response in replies.items():
        text += f"🔑 {keyword}\n💬 {response[:50]}...\n\n"
    
    await callback.message.edit_text(
        text[:4000],
        reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]])
    )

@app.on_callback_query(filters.regex(r"^(deleteReply)$"))
async def delete_reply(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    replies = users.get(str(user_id), {}).get("custom_replies", {})
    
    if not replies:
        return await callback.answer("📭 لا توجد ردود للحذف", show_alert=True)
    
    await callback.message.delete()
    
    try:
        keyword = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text=f"🔑 **اختر الكلمة المفتاحية للحذف**\n\nالموجودة: {', '.join(replies.keys())}\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]]))
    
    if keyword.text == "/cancel":
        return await keyword.reply("✅ تم الإلغاء")
    
    if keyword.text in replies:
        del users[str(user_id)]["custom_replies"][keyword.text]
        write(users_db, users)
        await keyword.reply(f"✅ تم حذف الرد للكلمة: {keyword.text}",
                          reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]]))
    else:
        await keyword.reply(f"❌ الكلمة '{keyword.text}' غير موجودة",
                          reply_markup=Markup([[Button("- العوده -", callback_data="autoReplies")]]))

# =================== تخصيص الرسائل ===================
@app.on_callback_query(filters.regex(r"^(customMessages)$"))
async def custom_messages_menu(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "📝 **تخصيص الرسائل**\n\n"
        "قم بتخصيص رسائل الترحيب والتحفيز التي يرسلها البوت:",
        reply_markup=get_custom_messages_markup(user_id)
    )

@app.on_callback_query(filters.regex(r"^(changeWelcome)$"))
async def change_welcome(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        msg = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="📝 **أرسل نص رسالة الترحيب الجديدة**\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=120
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]]))
    
    if msg.text == "/cancel":
        return await msg.reply("✅ تم الإلغاء")
    
    users[str(user_id)]["custom_welcome"] = msg.text
    write(users_db, users)
    
    await msg.reply("✅ تم تحديث رسالة الترحيب",
                   reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]]))

@app.on_callback_query(filters.regex(r"^(changeMotivation)$"))
async def change_motivation(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        msg = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="📝 **أرسل نص رسالة التحفيز الجديدة**\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=120
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]]))
    
    if msg.text == "/cancel":
        return await msg.reply("✅ تم الإلغاء")
    
    users[str(user_id)]["custom_motivation"] = msg.text
    write(users_db, users)
    
    await msg.reply("✅ تم تحديث رسالة التحفيز",
                   reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]]))

@app.on_callback_query(filters.regex(r"^(viewCustomMessages)$"))
async def view_custom_messages(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.get(str(user_id), {})
    
    welcome = user_data.get("custom_welcome", "❌ غير مخصص (افتراضي)")
    motivation = user_data.get("custom_motivation", "❌ غير مخصص (افتراضي)")
    
    text = f"📝 **الرسائل المخصصة:**\n\n"
    text += f"**رسالة الترحيب:**\n{welcome}\n\n"
    text += f"**رسالة التحفيز:**\n{motivation}\n\n"
    text += "💡 الرسائل الافتراضية تستخدم عند عدم التخصيص"
    
    await callback.message.edit_text(
        text[:4000],
        reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]])
    )

@app.on_callback_query(filters.regex(r"^(resetMessages)$"))
async def reset_messages(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if "custom_welcome" in users[str(user_id)]:
        del users[str(user_id)]["custom_welcome"]
    if "custom_motivation" in users[str(user_id)]:
        del users[str(user_id)]["custom_motivation"]
    
    write(users_db, users)
    await callback.answer("✅ تم استعادة الرسائل الافتراضية", show_alert=True)
    await custom_messages_menu(_, callback)

# =================== دالة الإرسال المحسنة ===================
async def send_to_group(client: Client, user_id: int, group_id: int, caption: str, invite_link: Optional[str] = None) -> bool:
    """إرسال رسالة إلى المجموعة مع حماية متكاملة"""
    user_id_str = str(user_id)
    global failed_groups
    
    if (user_id_str, group_id) in failed_groups:
        return False
    
    try:
        sent_msg = await client.send_message(group_id, caption)
        
        delete_after = users[user_id_str].get("delete_after", 0)
        if delete_after > 0:
            create_task(delete_message_after(sent_msg, delete_after))
        
        print(f"✅ تم الإرسال إلى المجموعة: {group_id}")
        return True
        
    except (PeerIdInvalid, ChatWriteForbidden, UserNotParticipant) as e:
        joined = False
        
        if invite_link:
            try:
                await client.join_chat(invite_link)
                joined = True
                print(f"✅ تم الانضمام عبر الرابط: {invite_link}")
            except Exception as join_err:
                print(f"فشل الانضمام عبر الرابط: {join_err}")
        
        if not joined:
            try:
                await client.join_chat(group_id)
                joined = True
                print(f"✅ تم الانضمام عبر المعرف: {group_id}")
            except Exception as join_err:
                print(f"فشل الانضمام عبر المعرف: {join_err}")
        
        if joined:
            try:
                sent_msg = await client.send_message(group_id, caption)
                delete_after = users[user_id_str].get("delete_after", 0)
                if delete_after > 0:
                    create_task(delete_message_after(sent_msg, delete_after))
                print(f"✅ تم الإرسال بعد الانضمام إلى: {group_id}")
                return True
            except Exception as send_err:
                print(f"فشل الإرسال بعد الانضمام: {send_err}")
        
        failed_groups.add((user_id_str, group_id))
        await app.send_message(user_id, f"❌ فشل الوصول إلى المجموعة {group_id}")
        return False
        
    except FloodWait as e:
        await app.send_message(user_id, f"⚠️ انتظر {e.value} ثانية")
        await sleep(e.value)
        return await send_to_group(client, user_id, group_id, caption, invite_link)
        
    except Exception as e:
        error_type = type(e).__name__
        print(f"⚠️ خطأ: {error_type} - {e}")
        return False

async def delete_message_after(message: Message, seconds: int):
    """حذف رسالة بعد وقت محدد"""
    await sleep(seconds)
    try:
        await message.delete()
    except:
        pass

# =================== دالة النشر الرئيسية ===================
async def posting(user_id: int):
    """نشر تلقائي متقدم - يرسل لجميع المجموعات"""
    user_id_str = str(user_id)
    
    if not users.get(user_id_str, {}).get("posting"):
        return
    
    client = Client(user_id_str, api_id=app.api_id, api_hash=app.api_hash, 
                    session_string=users[user_id_str]["session"])
    await client.start()
    
    try:
        while users[user_id_str].get("posting"):
            total_time = users[user_id_str].get("waitTime", 60)
            groups_data = users[user_id_str].get("groups", []).copy()
            captions_list = users[user_id_str].get("captions", []).copy()
            distribution_method = users[user_id_str].get("distribution_method", "random")
            
            if not captions_list:
                users[user_id_str]["posting"] = False
                write(users_db, users)
                await app.send_message(user_id, "❌ تم إيقاف النشر: لا توجد كليشات")
                break
            
            if not groups_data:
                users[user_id_str]["posting"] = False
                write(users_db, users)
                await app.send_message(user_id, "❌ تم إيقاف النشر: لا توجد مجموعات")
                break
            
            num_groups = len(groups_data)
            await app.send_message(user_id, f"🚀 بدء دورة نشر جديدة\n📊 عدد المجموعات: {num_groups}\n⏱️ المدة الإجمالية: {total_time} ثانية")
            
            random.shuffle(groups_data)
            delays = calculate_distributed_delays(num_groups, total_time, distribution_method)
            available_captions = captions_list.copy()
            
            for idx, group_obj in enumerate(groups_data):
                if not users[user_id_str].get("posting"):
                    break
                
                group_id = group_obj["id"]
                invite_link = group_obj.get("link")
                
                if not available_captions:
                    available_captions = captions_list.copy()
                
                chosen_caption = random.choice(available_captions)
                available_captions.remove(chosen_caption)
                
                success = await send_to_group(client, user_id, group_id, chosen_caption, invite_link)
                
                if success:
                    await app.send_message(user_id, f"✅ تم الإرسال إلى المجموعة {idx+1}/{num_groups}")
                else:
                    await app.send_message(user_id, f"❌ فشل الإرسال إلى المجموعة {idx+1}/{num_groups}")
                
                if idx < len(delays) - 1:
                    wait_time = delays[idx]
                    await app.send_message(user_id, f"⏳ انتظار {wait_time:.1f} ثانية قبل المجموعة التالية...")
                    await sleep(wait_time)
            
            await app.send_message(user_id, f"⏸️ اكتملت الدورة، انتظار {total_time} ثانية قبل الدورة التالية...")
            await sleep(total_time)
            
    except Exception as e:
        print(f"خطأ في النشر: {e}")
        await app.send_message(user_id, f"⚠️ حدث خطأ: {type(e).__name__}")
    finally:
        await client.stop()

# =================== أوامر المستخدم ===================
@app.on_message(filters.command("start") & filters.private)
async def start(_: Client, message: Message):
    user_id = message.from_user.id
    
    subscribed = await subscription(message)
    if isinstance(subscribed, str):
        return await message.reply(f"⚠️ عليك الإشتراك بقناة البوت أولاً\n📢 القناة: @{subscribed}\nاشترك ثم ارسل /start")
    
    if str(user_id) not in users:
        users[str(user_id)] = {
            "vip": True if user_id == owner else False,
            "smart_delay": True,
            "captions": [],
            "groups": [],
            "distribution_method": "random",
            "delete_after": 0,
            "waitTime": 60,
            "auto_reply_enabled": True,
            "custom_replies": {}
        }
        write(users_db, users)
    
    if user_id != owner and not users[str(user_id)].get("vip", False):
        return await message.reply(f"⚠️ لا يمكنك استخدام هذا البوت\n👤 تواصل مع [المطور](tg://openmessage?user_id={owner}) لتفعيل الإشتراك")
    
    fname = message.from_user.first_name
    caption = f"✨ مرحبا [{fname}](tg://settings)\n🤖 بوت النشر التلقائي\n📝 استخدم الأزرار للتحكم:"
    await message.reply(caption, reply_markup=get_home_markup(user_id))

@app.on_callback_query(filters.regex(r"^(toHome)$"))
async def toHome(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    fname = callback.from_user.first_name
    caption = f"✨ مرحبا [{fname}](tg://settings)\n🤖 بوت النشر التلقائي"
    await callback.message.edit_text(caption, reply_markup=get_home_markup(user_id))

# =================== إدارة الحساب ===================
@app.on_callback_query(filters.regex(r"^(account)$"))
async def account(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    has_session = users[str(user_id)].get("session") is not None
    status = "✅ مسجل" if has_session else "❌ غير مسجل"
    
    caption = f"👤 **الحساب**\n\nالحالة: {status}"
    markup = Markup([
        [Button("- تسجيل حساب -", callback_data="login")],
        [Button("- تغيير الحساب -", callback_data="changeAccount")] if has_session else [],
        [Button("- العوده -", callback_data="toHome")]
    ])
    await callback.message.edit_text(caption, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^(login|changeAccount)$"))
async def login(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="📱 أرسل رقم هاتفك مع رمز الدولة\nمثال: +966512345678\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="account")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("✅ تم الإلغاء")
    
    await registration(ask)

async def registration(message: Message):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    msg = await message.reply("🔄 جاري تسجيل الدخول...")
    
    client = Client("temp", in_memory=True, api_id=app.api_id, api_hash=app.api_hash)
    await client.connect()
    
    try:
        sent_code = await client.send_code(phone)
    except PhoneNumberInvalid:
        return await msg.edit("❌ رقم الهاتف غير صحيح")
    
    try:
        code = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="🔑 تم إرسال الكود. أرسله الآن:",
            reply_markup=ForceReply(selective=True),
            timeout=120
        )
    except exceptions.TimeOut:
        return await msg.edit("⏰ انتهى وقت الكود")
    
    try:
        await client.sign_in(phone, sent_code.phone_code_hash, code.text)
    except SessionPasswordNeeded:
        try:
            password = await listener.listen(
                from_id=user_id, chat_id=user_id,
                text="🔒 حسابك مفعل بالتحقق بخطوتين\nأرسل كلمة المرور:",
                reply_markup=ForceReply(selective=True),
                timeout=60
            )
        except exceptions.TimeOut:
            return await msg.edit("⏰ انتهى الوقت")
        await client.check_password(password.text)
    
    session = await client.export_session_string()
    await client.disconnect()
    
    users[str(user_id)]["session"] = session
    write(users_db, users)
    
    await app.send_message(user_id, "✅ تم تسجيل الدخول بنجاح", 
                          reply_markup=Markup([[Button("- الرئيسيه -", callback_data="toHome")]]))

# =================== إدارة السوبرات ===================
@app.on_callback_query(filters.regex(r"^(newSuper)$"))
async def newSuper(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="➕ أرسل رابط أو معرف المجموعة\nمثال: @username أو https://t.me/username\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="toHome")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("✅ تم الإلغاء")
    
    input_text = ask.text.strip()
    group_id = None
    invite_link = None
    
    if input_text.startswith("@"):
        username = input_text[1:]
        try:
            chat = await app.get_chat(username)
            group_id = chat.id
            invite_link = input_text
        except:
            return await ask.reply("❌ لم يتم العثور على المجموعة")
    
    elif "t.me/" in input_text:
        username = input_text.split("t.me/")[-1]
        try:
            chat = await app.get_chat(username)
            group_id = chat.id
            invite_link = input_text
        except:
            return await ask.reply("❌ رابط غير صالح")
    
    elif input_text.lstrip("-").isdigit():
        group_id = int(input_text)
    
    else:
        return await ask.reply("❌ صيغة غير صالحة")
    
    if group_id:
        if "groups" not in users[str(user_id)]:
            users[str(user_id)]["groups"] = []
        
        existing = [g for g in users[str(user_id)]["groups"] if g["id"] == group_id]
        if existing:
            return await ask.reply("⚠️ هذه المجموعة موجودة بالفعل")
        
        users[str(user_id)]["groups"].append({"id": group_id, "link": invite_link})
        write(users_db, users)
        
        try:
            chat = await app.get_chat(group_id)
            title = chat.title
        except:
            title = str(group_id)
        
        await ask.reply(f"✅ تم إضافة المجموعة: {title}\n📊 العدد الحالي: {len(users[str(user_id)]['groups'])}",
                       reply_markup=Markup([[Button("- الرئيسيه -", callback_data="toHome")]]))

@app.on_callback_query(filters.regex(r"^(currentSupers)$"))
async def currentSupers(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    groups = users[str(user_id)].get("groups", [])
    
    if not groups:
        return await callback.answer("📭 لا توجد مجموعات", show_alert=True)
    
    markup = []
    for g in groups:
        try:
            chat = await app.get_chat(g["id"])
            title = chat.title[:25]
        except:
            title = str(g["id"])[:25]
        markup.append([Button(f"📢 {title}", callback_data=f"super_{g['id']}"), 
                      Button("🗑️", callback_data=f"delSuper_{g['id']}")])
    
    markup.append([Button("- الرئيسيه -", callback_data="toHome")])
    await callback.message.edit_text(f"📋 **المجموعات ({len(groups)})**:", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^delSuper_"))
async def delSuper(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    gid = int(callback.data.split("_")[1])
    
    groups = users[str(user_id)].get("groups", [])
    users[str(user_id)]["groups"] = [g for g in groups if g["id"] != gid]
    write(users_db, users)
    
    await callback.answer("✅ تم الحذف", show_alert=True)
    await currentSupers(_, callback)

# =================== إدارة الكليشات ===================
@app.on_callback_query(filters.regex(r"^(manageCaptions)$"))
async def manageCaptions(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    captions = users[str(user_id)].get("captions", [])
    
    markup = []
    for idx, cap in enumerate(captions):
        short = cap[:20] + "..." if len(cap) > 20 else cap
        markup.append([Button(f"📝 {short}", callback_data=f"viewCap_{idx}"), 
                      Button("🗑️", callback_data=f"delCap_{idx}")])
    
    markup.append([Button("➕ إضافة كليشة", callback_data="addCaption")])
    markup.append([Button("- الرئيسيه -", callback_data="toHome")])
    
    count = len(captions)
    if count == 0:
        await callback.message.edit_text("📭 **لا توجد كليشات**\n➕ أضف كليشة جديدة:", reply_markup=Markup(markup))
    else:
        await callback.message.edit_text(f"📝 **الكليشات ({count})**:", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^(addCaption)$"))
async def addCaption(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="📝 أرسل نص الكليشة الجديدة\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=120
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="manageCaptions")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("✅ تم الإلغاء")
    
    captions = users[str(user_id)].get("captions", [])
    captions.append(ask.text)
    users[str(user_id)]["captions"] = captions
    write(users_db, users)
    
    await ask.reply(f"✅ تم إضافة الكليشة\n📊 العدد الحالي: {len(captions)}",
                   reply_markup=Markup([[Button("- العوده -", callback_data="manageCaptions")]]))

@app.on_callback_query(filters.regex(r"^delCap_"))
async def delCaption(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    idx = int(callback.data.split("_")[1])
    
    captions = users[str(user_id)].get("captions", [])
    if 0 <= idx < len(captions):
        captions.pop(idx)
        users[str(user_id)]["captions"] = captions
        write(users_db, users)
        await callback.answer("✅ تم الحذف", show_alert=True)
    
    await manageCaptions(_, callback)

@app.on_callback_query(filters.regex(r"^viewCap_"))
async def viewCaption(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    idx = int(callback.data.split("_")[1])
    
    captions = users[str(user_id)].get("captions", [])
    if 0 <= idx < len(captions):
        await callback.answer("📄 معاينة:", show_alert=True)
        await callback.message.reply(f"**نص الكليشة:**\n{captions[idx]}", 
                                    reply_markup=Markup([[Button("- العوده -", callback_data="manageCaptions")]]))

# =================== إعدادات النشر ===================
@app.on_callback_query(filters.regex(r"^(waitTime)$"))
async def waitTime(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("waitTime", 60)
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text=f"⏱️ **المدة الحالية:** {current} ثانية\n\nأرسل المدة الجديدة (بالثواني)\nالحد الأدنى: 10 ثوانٍ\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="toHome")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("✅ تم الإلغاء")
    
    try:
        wait = int(ask.text)
        if wait < 10:
            return await ask.reply("⚠️ المدة يجب أن تكون 10 ثوانٍ على الأقل")
        users[str(user_id)]["waitTime"] = wait
        write(users_db, users)
        await ask.reply(f"✅ تم تعيين المدة: {wait} ثانية", 
                       reply_markup=Markup([[Button("- الرئيسيه -", callback_data="toHome")]]))
    except ValueError:
        await ask.reply("❌ أرسل رقماً صحيحاً")

@app.on_callback_query(filters.regex(r"^(deleteTime)$"))
async def deleteTime(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("delete_after", 0)
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text=f"🗑️ **مدة الحذف الحالية:** {current if current > 0 else 'معطل'}\n\nأرسل المدة الجديدة (بالثواني)\n0 = تعطيل الحذف\n/cancel للإلغاء",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="toHome")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("✅ تم الإلغاء")
    
    try:
        delete_after = int(ask.text)
        if delete_after < 0:
            return await ask.reply("⚠️ أدخل قيمة 0 أو أكثر")
        users[str(user_id)]["delete_after"] = delete_after
        write(users_db, users)
        status = "معطل" if delete_after == 0 else f"{delete_after} ثانية"
        await ask.reply(f"✅ تم تعيين مدة الحذف: {status}", 
                       reply_markup=Markup([[Button("- الرئيسيه -", callback_data="toHome")]]))
    except ValueError:
        await ask.reply("❌ أرسل رقماً صحيحاً")

@app.on_callback_query(filters.regex(r"^(distributionMethod)$"))
async def distributionMethod(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text("📊 **اختر طريقة توزيع الفروق الزمنية:**", 
                                    reply_markup=get_distribution_markup(user_id))

@app.on_callback_query(filters.regex(r"^setDist_"))
async def setDistribution(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    method = callback.data.split("_")[1]
    
    users[str(user_id)]["distribution_method"] = method
    write(users_db, users)
    
    method_names = {"equal": "المتساوي", "random": "العشوائي", "fibonacci": "فيبوناتشي"}
    await callback.answer(f"✅ تم تعيين طريقة {method_names[method]}", show_alert=True)
    await distributionMethod(_, callback)

@app.on_callback_query(filters.regex(r"^(toggleSmartDelay)$"))
async def toggleSmartDelay(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("smart_delay", True)
    users[str(user_id)]["smart_delay"] = not current
    write(users_db, users)
    await callback.answer(f"✅ تم {'تفعيل' if not current else 'تعطيل'} التأخير الذكي", show_alert=True)
    await toHome(_, callback)

# =================== بدء وإيقاف النشر ===================
@app.on_callback_query(filters.regex(r"^(startPosting)$"))
async def startPosting(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if not users[str(user_id)].get("session"):
        return await callback.answer("❌ يجب تسجيل حساب أولاً", show_alert=True)
    
    if not users[str(user_id)].get("groups"):
        return await callback.answer("❌ يجب إضافة مجموعات أولاً", show_alert=True)
    
    if not users[str(user_id)].get("captions"):
        return await callback.answer("❌ يجب إضافة كليشات أولاً", show_alert=True)
    
    if users[str(user_id)].get("posting"):
        return await callback.answer("⚠️ النشر مفعل بالفعل", show_alert=True)
    
    users[str(user_id)]["posting"] = True
    write(users_db, users)
    
    task = create_task(posting(user_id))
    active_tasks.add(str(user_id))
    task.add_done_callback(lambda t: active_tasks.discard(str(user_id)))
    
    groups_count = len(users[str(user_id)]["groups"])
    captions_count = len(users[str(user_id)]["captions"])
    wait_time = users[str(user_id)].get("waitTime", 60)
    
    await callback.message.edit_text(
        f"🚀 **بدء النشر التلقائي**\n\n"
        f"📊 المجموعات: {groups_count}\n"
        f"📝 الكليشات: {captions_count}\n"
        f"⏱️ المدة: {wait_time} ثانية\n\n"
        f"✅ سيتم الإرسال لجميع المجموعات",
        reply_markup=Markup([[Button("⏹️ إيقاف", callback_data="stopPosting"), 
                             Button("🏠 الرئيسيه", callback_data="toHome")]])
    )

@app.on_callback_query(filters.regex(r"^(stopPosting)$"))
async def stopPosting(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if not users[str(user_id)].get("posting"):
        return await callback.answer("⚠️ النشر معطل بالفعل", show_alert=True)
    
    users[str(user_id)]["posting"] = False
    write(users_db, users)
    
    await callback.message.edit_text("🛑 **تم إيقاف النشر التلقائي**", 
                                    reply_markup=Markup([[Button("▶️ بدء", callback_data="startPosting"), 
                                                         Button("🏠 الرئيسيه", callback_data="toHome")]]))

# =================== قسم المالك ===================
async def isOwner(_, __, message: Message) -> bool:
    return message.from_user.id == owner

owner_filter = filters.create(isOwner)

@app.on_message(filters.command("admin") & filters.private & owner_filter)
async def adminPanel(_: Client, message: Message):
    await message.reply("👑 **لوحة تحكم المالك**", reply_markup=Markup([
        [Button("➕ تفعيل VIP", callback_data="addVIP"), Button("➖ الغاء VIP", callback_data="cancelVIP")],
        [Button("📊 الاحصائيات", callback_data="statics"), Button("📢 قنوات الإشتراك", callback_data="channels")],
        [Button("🛡️ حماية الخصوصية", callback_data="privacyProtection")],
        [Button("📝 إدارة الرسائل العامة", callback_data="globalMessages")]
    ]))

@app.on_callback_query(filters.regex("addVIP") & owner_filter)
async def addVIP(_: Client, callback: CallbackQuery):
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=owner, chat_id=owner,
            text="👤 أرسل ايدي المستخدم",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت")
    
    try:
        user_id = int(ask.text)
    except:
        return await ask.reply("❌ ايدي غير صالح")
    
    try:
        days = await listener.listen(
            from_id=owner, chat_id=owner,
            text="📅 أرسل عدد الأيام",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت")
    
    try:
        limit_days = int(days.text)
    except:
        return await days.reply("❌ أرسل رقماً صحيحاً")
    
    if str(user_id) not in users:
        users[str(user_id)] = {"vip": True, "smart_delay": True, "captions": [], "groups": [], "waitTime": 60, "auto_reply_enabled": True, "custom_replies": {}}
    else:
        users[str(user_id)]["vip"] = True
    
    end_date = datetime.now(_timezone) + timedelta(days=limit_days)
    users[str(user_id)]["limitation"] = {
        "days": limit_days,
        "endDate": end_date.strftime("%Y-%m-%d"),
        "endTime": end_date.strftime("%H:%M")
    }
    write(users_db, users)
    
    await days.reply(f"✅ تم تفعيل VIP للمستخدم {user_id}\n📅 المدة: {limit_days} يوم",
                    reply_markup=Markup([[Button("- العوده -", callback_data="admin")]]))

@app.on_callback_query(filters.regex("cancelVIP") & owner_filter)
async def cancelVIP(_: Client, callback: CallbackQuery):
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=owner, chat_id=owner,
            text="👤 أرسل ايدي المستخدم",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت")
    
    user_id = ask.text
    if user_id in users:
        users[user_id]["vip"] = False
        write(users_db, users)
        await ask.reply(f"✅ تم الغاء VIP للمستخدم {user_id}",
                       reply_markup=Markup([[Button("- العوده -", callback_data="admin")]]))
    else:
        await ask.reply("❌ المستخدم غير موجود")

@app.on_callback_query(filters.regex("statics") & owner_filter)
async def statics(_: Client, callback: CallbackQuery):
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip", False))
    posting = sum(1 for u in users.values() if u.get("posting", False))
    total_groups = sum(len(u.get("groups", [])) for u in users.values())
    total_captions = sum(len(u.get("captions", [])) for u in users.values())
    auto_reply_active = sum(1 for u in users.values() if u.get("auto_reply_enabled", True))
    
    await callback.message.edit_text(
        f"📊 **الإحصائيات**\n\n"
        f"👥 إجمالي المستخدمين: {total}\n"
        f"⭐ مستخدمي VIP: {vip}\n"
        f"🚀 النشر مفعل: {posting}\n"
        f"📢 إجمالي المجموعات: {total_groups}\n"
        f"📝 إجمالي الكليشات: {total_captions}\n"
        f"💬 الردود التلقائية مفعلة: {auto_reply_active}",
        reply_markup=Markup([[Button("- العوده -", callback_data="admin")]])
    )

@app.on_callback_query(filters.regex("channels") & owner_filter)
async def channelsControl(_: Client, callback: CallbackQuery):
    markup = []
    for ch in channels:
        markup.append([Button(f"📢 @{ch}", url=f"https://t.me/{ch}"), 
                      Button("🗑️", callback_data=f"removeChannel_{ch}")])
    markup.append([Button("➕ إضافة قناة", callback_data="addChannel")])
    markup.append([Button("- العوده -", callback_data="admin")])
    
    await callback.message.edit_text("📢 **قنوات الإشتراك الإجباري**", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex("addChannel") & owner_filter)
async def addChannel(_: Client, callback: CallbackQuery):
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=owner, chat_id=owner,
            text="📢 أرسل معرف القناة (بدون @)\nمثال: channelusername",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("⏰ انتهى الوقت")
    
    channel = ask.text.strip()
    channels.append(channel)
    write(channels_db, channels)
    
    await ask.reply(f"✅ تم إضافة قناة @{channel}",
                   reply_markup=Markup([[Button("- العوده -", callback_data="channels")]]))

@app.on_callback_query(filters.regex("removeChannel_") & owner_filter)
async def removeChannel(_: Client, callback: CallbackQuery):
    channel = callback.data.split("_")[1]
    if channel in channels:
        channels.remove(channel)
        write(channels_db, channels)
        await callback.answer("✅ تم الحذف", show_alert=True)
    await channelsControl(_, callback)

@app.on_callback_query(filters.regex("privacyProtection") & owner_filter)
async def privacyProtection(_: Client, callback: CallbackQuery):
    global privacy_protection_active
    privacy_protection_active = not privacy_protection_active
    
    status = "مفعلة ✅" if privacy_protection_active else "معطلة ❌"
    await callback.answer(f"حماية الخصوصية {status}", show_alert=True)
    await callback.message.edit_text(
        f"🛡️ **حماية سياسة الخصوصية**\n\n"
        f"الحالة: {status}\n\n"
        f"عند التفعيل، يقوم البوت بالرد تلقائياً على أسئلة بوتات الخصوصية\n"
        f"بإجابات عشوائية تحاكي المستخدمين الحقيقيين.",
        reply_markup=Markup([[Button("- العوده -", callback_data="admin")]])
    )

@app.on_callback_query(filters.regex("globalMessages") & owner_filter)
async def globalMessages(_: Client, callback: CallbackQuery):
    await callback.message.edit_text(
        "📝 **إدارة الرسائل العامة**\n\n"
        "تحكم في الرسائل الافتراضية التي يرسلها البوت للجميع:",
        reply_markup=Markup([
            [Button("✏️ تغيير رسائل الترحيب العامة", callback_data="editGlobalWelcome")],
            [Button("✏️ تغيير رسائل التحفيز العامة", callback_data="editGlobalMotivation")],
            [Button("🔄 استعادة الافتراضي", callback_data="resetGlobalMessages")],
            [Button("- العوده -", callback_data="admin")]
        ])
    )

# =================== الإشتراك الإجباري ===================
async def subscription(message: Message) -> Union[bool, str]:
    user_id = message.from_user.id
    for channel in channels:
        try:
            await app.get_chat_member(channel, user_id)
        except UserNotParticipant:
            return channel
    return True

# =================== إدارة التخزين ===================
def write(file_path: str, data: Any):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read(file_path: str) -> Any:
    if not os.path.exists(file_path):
        write(file_path, {} if "users" in file_path else [])
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# =================== دوال إعادة التشغيل ===================
async def restartPosting():
    await sleep(30)
    for user_id, data in users.items():
        if data.get("posting") and str(user_id) not in active_tasks:
            task = create_task(posting(int(user_id)))
            active_tasks.add(str(user_id))
            task.add_done_callback(lambda t, uid=str(user_id): active_tasks.discard(uid))

async def checkVIPExpiry():
    while True:
        now = datetime.now(_timezone)
        for user_id, data in users.items():
            if data.get("vip") and "limitation" in data:
                end_date_str = f"{data['limitation']['endDate']} {data['limitation']['endTime']}"
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")
                end_date = _timezone.localize(end_date)
                
                if now >= end_date:
                    data["vip"] = False
                    write(users_db, users)
                    try:
                        await app.send_message(int(user_id), "⚠️ انتهت صلاحية الاشتراك VIP")
                    except:
                        pass
        await sleep(3600)

# =================== التشغيل الرئيسي ===================
_timezone = timezone("Asia/Baghdad")
users_db = "users.json"
channels_db = "channels.json"
users = read(users_db)
channels = read(channels_db)

async def main():
    print("🤖 تشغيل البوت...")
    print("📊 تحميل البيانات...")
    print(f"👥 المستخدمين المسجلين: {len(users)}")
    print(f"📢 القنوات الإجبارية: {len(channels)}")
    
    create_task(restartPosting())
    create_task(checkVIPExpiry())
    await app.start()
    
    bot_info = await app.get_me()
    print(f"✅ البوت يعمل بنجاح!")
    print(f"🤖 اسم البوت: {bot_info.first_name}")
    print(f"🆔 معرف البوت: {bot_info.id}")
    print(f"👑 المطور: {owner}")
    print(f"📊 المستخدمين: {len(users)}")
    print("💡 تم تفعيل الردود التلقائية للرسائل الخاصة")
    print("📝 تم تفعيل تخصيص الرسائل")
    
    await idle()

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت")
    except Exception as e:
        print(f"❌ خطأ: {e}")
