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
import asyncio
from asyncio import create_task, sleep, get_event_loop
from datetime import datetime, timedelta
from pytz import timezone
from typing import Union, List, Dict, Any, Optional
import json, random, re

# =================== إعدادات البوت ===================
app = Client(
    "autoPost",
    api_id=34923196,
    api_hash="b3f6e47ecd3231186f8f7e01ab41938e",
    bot_token='8832559640:AAGGV15XucCuMgQ20StPFGPv8LYANTnb0bc'
)

# =================== المتغيرات العامة ===================
owner = 8310839908
active_tasks = set()
failed_groups = set()
privacy_protection_active = True

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

# =================== إدارة التخزين ===================
def write(file_path: str, data: Any):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read(file_path: str) -> Any:
    if not os.path.exists(file_path):
        if "users" in file_path:
            write(file_path, {})
        else:
            write(file_path, [])
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# =================== تحميل البيانات ===================
_timezone = timezone("Asia/Baghdad")
users_db = "users.json"
channels_db = "channels.json"
users = read(users_db)
channels = read(channels_db)

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

def get_greeting_response(text: str) -> Optional[str]:
    """الحصول على رد مناسب للتحية"""
    text_lower = text.lower().strip()
    
    for greeting, response in GREETING_RESPONSES.items():
        if greeting.lower() in text_lower:
            return response
    
    greeting_words = ["سلام", "هلا", "مرحب", "اهلا", "هاي", "hello", "hi", "hey"]
    for word in greeting_words:
        if word in text_lower:
            return GREETING_RESPONSES.get(word.capitalize(), "وعليكم السلام")
    
    return None

# =================== معالجة الرسائل الخاصة ===================
@app.on_message(filters.private & filters.text & ~filters.command(["start", "admin"]))
async def handle_private_messages(client: Client, message: Message):
    """معالجة جميع الرسائل الخاصة"""
    user_id = message.from_user.id
    text = message.text
    
    # تجاهل رسائل البوت نفسه
    if user_id == (await client.get_me()).id:
        return
    
    # تجاهل الأوامر
    if text.startswith('/'):
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
        await asyncio.sleep(random.uniform(1, 3))
        
        # الحصول على رسائل مخصصة أو الافتراضية
        custom_welcome = user_data.get("custom_welcome", None)
        custom_motivation = user_data.get("custom_motivation", None)
        
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
    me = await app.get_me()
    await callback.message.edit_text(
        "💬 **للتواصل عبر التيليجرام:**\n\n"
        "يمكنك مراسلة المطور مباشرة:\n"
        f"👤 @{me.username}\n\n"
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
        msg = await app.wait_for_message(
            chat_id=user_id,
            text="📝 **أرسل نص رسالة الترحيب الجديدة**\n/إلغاء للإلغاء",
            timeout=120
        )
    except asyncio.TimeoutError:
        return await app.send_message(user_id, "⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]]))
    
    if msg.text == "/إلغاء":
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
        msg = await app.wait_for_message(
            chat_id=user_id,
            text="📝 **أرسل نص رسالة التحفيز الجديدة**\n/إلغاء للإلغاء",
            timeout=120
        )
    except asyncio.TimeoutError:
        return await app.send_message(user_id, "⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="customMessages")]]))
    
    if msg.text == "/إلغاء":
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

# =================== حساب المستخدم ===================
@app.on_message(filters.command("start") & filters.private)
async def start(_: Client, message: Message):
    user_id = message.from_user.id
    
    # التحقق من الإشتراك
    subscribed = await subscription(message)
    if isinstance(subscribed, str):
        return await message.reply(f"⚠️ عليك الإشتراك بقناة البوت أولاً\n📢 القناة: @{subscribed}\nاشترك ثم ارسل /start")
    
    # إنشاء حساب جديد
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
            "custom_replies": {},
            "session": None
        }
        write(users_db, users)
    
    # التحقق من الـ VIP
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

# =================== إدارة السوبرات ===================
@app.on_callback_query(filters.regex(r"^(newSuper)$"))
async def newSuper(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await app.wait_for_message(
            chat_id=user_id,
            text="➕ أرسل رابط أو معرف المجموعة\nمثال: @username أو https://t.me/username\n/إلغاء للإلغاء",
            timeout=60
        )
    except asyncio.TimeoutError:
        return await app.send_message(user_id, "⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="toHome")]]))
    
    if ask.text == "/إلغاء":
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
        ask = await app.wait_for_message(
            chat_id=user_id,
            text="📝 أرسل نص الكليشة الجديدة\n/إلغاء للإلغاء",
            timeout=120
        )
    except asyncio.TimeoutError:
        return await app.send_message(user_id, "⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="manageCaptions")]]))
    
    if ask.text == "/إلغاء":
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

# =================== إعدادات النشر ===================
@app.on_callback_query(filters.regex(r"^(waitTime)$"))
async def waitTime(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("waitTime", 60)
    await callback.message.delete()
    
    try:
        ask = await app.wait_for_message(
            chat_id=user_id,
            text=f"⏱️ **المدة الحالية:** {current} ثانية\n\nأرسل المدة الجديدة (بالثواني)\nالحد الأدنى: 10 ثوانٍ\n/إلغاء للإلغاء",
            timeout=60
        )
    except asyncio.TimeoutError:
        return await app.send_message(user_id, "⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="toHome")]]))
    
    if ask.text == "/إلغاء":
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
        ask = await app.wait_for_message(
            chat_id=user_id,
            text=f"🗑️ **مدة الحذف الحالية:** {current if current > 0 else 'معطل'}\n\nأرسل المدة الجديدة (بالثواني)\n0 = تعطيل الحذف\n/إلغاء للإلغاء",
            timeout=60
        )
    except asyncio.TimeoutError:
        return await app.send_message(user_id, "⏰ انتهى الوقت", reply_markup=Markup([[Button("- العوده -", callback_data="toHome")]]))
    
    if ask.text == "/إلغاء":
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

# =================== الإشتراك الإجباري ===================
async def subscription(message: Message) -> Union[bool, str]:
    user_id = message.from_user.id
    for channel in channels:
        try:
            await app.get_chat_member(channel, user_id)
        except UserNotParticipant:
            return channel
    return True

# =================== التشغيل الرئيسي ===================
async def main():
    print("🤖 تشغيل البوت...")
    print("📊 تحميل البيانات...")
    print(f"👥 المستخدمين المسجلين: {len(users)}")
    print(f"📢 القنوات الإجبارية: {len(channels)}")
    
    await app.start()
    
    bot_info = await app.get_me()
    print("=" * 40)
    print(f"✅ البوت يعمل بنجاح!")
    print(f"🤖 اسم البوت: {bot_info.first_name}")
    print(f"🆔 معرف البوت: {bot_info.id}")
    print(f"👑 المطور: {owner}")
    print(f"📊 المستخدمين: {len(users)}")
    print("💡 تم تفعيل الردود التلقائية للرسائل الخاصة")
    print("📝 تم تفعيل تخصيص الرسائل")
    print("=" * 40)
    
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت")
    except Exception as e:
        print(f"❌ خطأ: {e}")
