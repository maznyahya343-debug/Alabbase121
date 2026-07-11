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
import json, random, re

# =================== ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ط¨ظˆطھ ===================
app = Client(
    "autoPost",
    api_id="34923196",
    api_hash="b3f6e47ecd3231186f8f7e01ab41938e",
    bot_token='8832559640:AAGGV15XucCuMgQ20StPFGPv8LYANTnb0bc'
)
loop = get_event_loop()
listener = Listener(client=app)
owner = 8310839908

# =================== ط§ظ„ظ…طھط؛ظٹط±ط§طھ ط§ظ„ط¹ط§ظ…ط© ===================
active_tasks = set()
failed_groups = set()
privacy_protection_active = True

# =================== ط¯ظˆط§ظ„ ظ…ط³ط§ط¹ط¯ط© ===================
def get_home_markup(user_id: int) -> Markup:
    """ط¥ظ†ط´ط§ط، ط£ط²ط±ط§ط± ط§ظ„طµظپط­ط© ط§ظ„ط±ط¦ظٹط³ظٹط©"""
    user_data = users.get(str(user_id), {})
    delay_mode_text = "âœ… طھط£ط®ظٹط± ط°ظƒظٹ ظ…ظپط¹ظ„" if user_data.get("smart_delay", True) else "â‌Œ طھط£ط®ظٹط± ط°ظƒظٹ ظ…ط¹ط·ظ„"
    delete_mode_text = f"ًں—‘ï¸ڈ ط­ط°ظپ: {user_data.get('delete_after', 0)}ط«" if user_data.get('delete_after', 0) > 0 else "ًں—‘ï¸ڈ ط­ط°ظپ: ظ…ط¹ط·ظ„"
    
    return Markup([
        [Button("- ط­ط³ط§ط¨ظƒ -", callback_data="account")],
        [Button("- ط§ظ„ط³ظˆط¨ط±ط§طھ -", callback_data="currentSupers"), Button("â‍• ط¥ط¶ط§ظپط©", callback_data="newSuper")],
        [Button("- ط§ظ„ظ…ط¯ط© ط¨ظٹظ† ط§ظ„ظ†ط´ط± -", callback_data="waitTime"), Button("- ط§ظ„ظƒظ„ظٹط´ط§طھ -", callback_data="manageCaptions")],
        [Button("- ط·ط±ظٹظ‚ط© ط§ظ„طھظˆط²ظٹط¹ -", callback_data="distributionMethod")],
        [Button(delete_mode_text, callback_data="deleteTime")],
        [Button("âڈ¹ï¸ڈ ط¥ظٹظ‚ط§ظپ", callback_data="stopPosting"), Button("â–¶ï¸ڈ ط¨ط¯ط،", callback_data="startPosting")],
        [Button(delay_mode_text, callback_data="toggleSmartDelay")]
    ])

def get_distribution_markup(user_id: int) -> Markup:
    """ط¥ظ†ط´ط§ط، ط£ط²ط±ط§ط± ط·ط±ظ‚ ط§ظ„طھظˆط²ظٹط¹ ط§ظ„ط²ظ…ظ†ظٹ"""
    current = users[str(user_id)].get("distribution_method", "random")
    methods = {
        "equal": "ًں“ڈ ظ…طھط³ط§ظˆظٹ",
        "random": "ًںژ² ط¹ط´ظˆط§ط¦ظٹ", 
        "fibonacci": "ًں“ˆ ظپظٹط¨ظˆظ†ط§طھط´ظٹ"
    }
    markup = []
    for key, name in methods.items():
        status = "âœ… " if current == key else "â‌Œ "
        markup.append([Button(f"{status}{name}", callback_data=f"setDist_{key}")])
    markup.append([Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")])
    return Markup(markup)

def calculate_distributed_delays(num_groups: int, total_time: int, method: str = "random") -> List[float]:
    """ط­ط³ط§ط¨ ط§ظ„ظپط±ظˆظ‚ ط§ظ„ط²ظ…ظ†ظٹط© ط¨ظٹظ† ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ ط­ط³ط¨ ط§ظ„ط·ط±ظٹظ‚ط© ط§ظ„ظ…ط®طھط§ط±ط©"""
    if num_groups <= 1:
        return [0]
    
    if method == "equal":
        # طھظˆط²ظٹط¹ ظ…طھط³ط§ظˆظٹ - ظƒظ„ ظ…ط¬ظ…ظˆط¹ط© طھظ†طھط¸ط± ظ†ظپط³ ط§ظ„ظ…ط¯ط©
        delay_per_group = total_time / num_groups
        return [delay_per_group] * num_groups
    
    elif method == "fibonacci":
        # طھظˆط²ظٹط¹ ظ…طھط²ط§ظٹط¯ ط­ط³ط¨ طھط³ظ„ط³ظ„ ظپظٹط¨ظˆظ†ط§طھط´ظٹ
        fib = [1, 1]
        for i in range(num_groups - 2):
            fib.append(fib[-1] + fib[-2])
        total_fib = sum(fib[:num_groups])
        return [(total_time * f / total_fib) for f in fib[:num_groups]]
    
    else:  # random
        # طھظˆط²ظٹط¹ ط¹ط´ظˆط§ط¦ظٹ
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

# =================== ط­ظ…ط§ظٹط© ط³ظٹط§ط³ط© ط§ظ„ط®طµظˆطµظٹط© ===================
PRIVACY_RESPONSES = [
    "ط§ط³ظ…ظٹ {name} ظ…ظ† {country} ط¹ظ…ط±ظٹ {age} ط³ظ†ط©",
    "ط£ظ†ط§ {name} ظ…ظ† {country}طŒ ط¹ظ…ط±ظٹ {age} ط³ظ†ط©",
    "ط§ظ„ط§ط³ظ…: {name}\nط§ظ„ط¹ظ…ط±: {age}\nط§ظ„ط¨ظ„ط¯: {country}",
    "{name}\n{age} ط³ظ†ط©\n{country}",
    "ظ…ط±ط­ط¨ط§ظ‹طŒ ط£ظ†ط§ {name}طŒ {age} ط¹ط§ظ…طŒ ظ…ظ† {country}",
    "ط£ظ†ط§ {name} - {age} ط³ظ†ط© - ظ…ظ† {country}"
]

COUNTRIES = ["ظ…طµط±", "ط§ظ„ط³ط¹ظˆط¯ظٹط©", "ط§ظ„ط¥ظ…ط§ط±ط§طھ", "ط§ظ„ظƒظˆظٹطھ", "ظ‚ط·ط±", "ط¹ظ…ط§ظ†", "ط§ظ„ط¨ط­ط±ظٹظ†", "ط§ظ„ط£ط±ط¯ظ†", "ط§ظ„ط¹ط±ط§ظ‚", "ط³ظˆط±ظٹط§", "ظ„ط¨ظ†ط§ظ†", "ظپظ„ط³ط·ظٹظ†", "ط§ظ„ظٹظ…ظ†", "ظ„ظٹط¨ظٹط§", "طھظˆظ†ط³", "ط§ظ„ط¬ط²ط§ط¦ط±", "ط§ظ„ظ…ط؛ط±ط¨", "ط§ظ„ط³ظˆط¯ط§ظ†"]
NAMES = ["ط£ط­ظ…ط¯", "ظ…ط­ظ…ط¯", "ط¹ظ„ظٹ", "ط­ط³ظ†", "ط­ط³ظٹظ†", "ط¹ظ…ط±", "ط¹ط«ظ…ط§ظ†", "ط®ط§ظ„ط¯", "ظٹظˆط³ظپ", "ط¥ط¨ط±ط§ظ‡ظٹظ…", "ظ…ط­ظ…ظˆط¯", "ظ…طµط·ظپظ‰", "ظƒط±ظٹظ…", "ط³ط¹ظٹط¯", "ظ†ط¨ظٹظ„"]
AGES = list(range(18, 65))

async def handle_privacy_bot(client: Client, message: Message, user_id: int) -> bool:
    """ظ…ط¹ط§ظ„ط¬ط© ط±ط³ط§ط¦ظ„ ط¨ظˆطھ ط³ظٹط§ط³ط© ط§ظ„ط®طµظˆطµظٹط© ط¨ط´ظƒظ„ ط°ظƒظٹ"""
    global privacy_protection_active
    
    if not privacy_protection_active:
        return False
    
    if not message.text:
        return False
        
    text = message.text.lower()
    
    # ظƒط´ظپ ظ†ظ…ط§ط°ط¬ ط§ظ„ط£ط³ط¦ظ„ط©
    privacy_keywords = [
        "tell me about yourself", "introduce yourself", "who are you",
        "what is your name", "how old are you", "where are you from",
        "your name", "your age", "your country", "tell us about you",
        "give me information", "personal information", "about you",
        "ط¹ط±ظپ ظ†ظپط³ظƒ", "ظ…ظ† ط§ظ†طھ", "ظ…ط§ ط§ط³ظ…ظƒ", "ظƒظ… ط¹ظ…ط±ظƒ", "ظ…ظ† ط§ظٹظ† ط§ظ†طھ",
        "ط§ط¹ط±ظپ ط¹ظ†ظƒ", "ظ…ط¹ظ„ظˆظ…ط§طھ ط¹ظ†ظƒ", "ط§ظ„ط§ط³ظ…", "ط§ظ„ط¹ظ…ط±", "ط§ظ„ط¨ظ„ط¯"
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

# =================== ط¯ط§ظ„ط© ط§ظ„ط¥ط±ط³ط§ظ„ ط§ظ„ظ…ط­ط³ظ†ط© ===================
async def send_to_group(client: Client, user_id: int, group_id: int, caption: str, invite_link: Optional[str] = None) -> bool:
    """ط¥ط±ط³ط§ظ„ ط±ط³ط§ظ„ط© ط¥ظ„ظ‰ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© ظ…ط¹ ط­ظ…ط§ظٹط© ظ…طھظƒط§ظ…ظ„ط©"""
    user_id_str = str(user_id)
    global failed_groups
    
    if (user_id_str, group_id) in failed_groups:
        return False
    
    try:
        sent_msg = await client.send_message(group_id, caption)
        
        delete_after = users[user_id_str].get("delete_after", 0)
        if delete_after > 0:
            create_task(delete_message_after(sent_msg, delete_after))
        
        print(f"âœ… طھظ… ط§ظ„ط¥ط±ط³ط§ظ„ ط¥ظ„ظ‰ ط§ظ„ظ…ط¬ظ…ظˆط¹ط©: {group_id}")
        return True
        
    except (PeerIdInvalid, ChatWriteForbidden, UserNotParticipant) as e:
        # ظ…ط­ط§ظˆظ„ط© ط§ظ„ط§ظ†ط¶ظ…ط§ظ… ظ„ظ„ظ…ط¬ظ…ظˆط¹ط©
        joined = False
        
        if invite_link:
            try:
                await client.join_chat(invite_link)
                joined = True
                print(f"âœ… طھظ… ط§ظ„ط§ظ†ط¶ظ…ط§ظ… ط¹ط¨ط± ط§ظ„ط±ط§ط¨ط·: {invite_link}")
            except Exception as join_err:
                print(f"ظپط´ظ„ ط§ظ„ط§ظ†ط¶ظ…ط§ظ… ط¹ط¨ط± ط§ظ„ط±ط§ط¨ط·: {join_err}")
        
        if not joined:
            try:
                await client.join_chat(group_id)
                joined = True
                print(f"âœ… طھظ… ط§ظ„ط§ظ†ط¶ظ…ط§ظ… ط¹ط¨ط± ط§ظ„ظ…ط¹ط±ظپ: {group_id}")
            except Exception as join_err:
                print(f"ظپط´ظ„ ط§ظ„ط§ظ†ط¶ظ…ط§ظ… ط¹ط¨ط± ط§ظ„ظ…ط¹ط±ظپ: {join_err}")
        
        if joined:
            try:
                sent_msg = await client.send_message(group_id, caption)
                delete_after = users[user_id_str].get("delete_after", 0)
                if delete_after > 0:
                    create_task(delete_message_after(sent_msg, delete_after))
                print(f"âœ… طھظ… ط§ظ„ط¥ط±ط³ط§ظ„ ط¨ط¹ط¯ ط§ظ„ط§ظ†ط¶ظ…ط§ظ… ط¥ظ„ظ‰: {group_id}")
                return True
            except Exception as send_err:
                print(f"ظپط´ظ„ ط§ظ„ط¥ط±ط³ط§ظ„ ط¨ط¹ط¯ ط§ظ„ط§ظ†ط¶ظ…ط§ظ…: {send_err}")
        
        failed_groups.add((user_id_str, group_id))
        await app.send_message(user_id, f"â‌Œ ظپط´ظ„ ط§ظ„ظˆطµظˆظ„ ط¥ظ„ظ‰ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© {group_id}")
        return False
        
    except FloodWait as e:
        await app.send_message(user_id, f"âڑ ï¸ڈ ط§ظ†طھط¸ط± {e.value} ط«ط§ظ†ظٹط©")
        await sleep(e.value)
        return await send_to_group(client, user_id, group_id, caption, invite_link)
        
    except Exception as e:
        error_type = type(e).__name__
        print(f"âڑ ï¸ڈ ط®ط·ط£: {error_type} - {e}")
        return False

async def delete_message_after(message: Message, seconds: int):
    """ط­ط°ظپ ط±ط³ط§ظ„ط© ط¨ط¹ط¯ ظˆظ‚طھ ظ…ط­ط¯ط¯"""
    await sleep(seconds)
    try:
        await message.delete()
    except:
        pass

# =================== ط¯ط§ظ„ط© ط§ظ„ظ†ط´ط± ط§ظ„ط±ط¦ظٹط³ظٹط© - ط§ظ„ط­ظ„ ط§ظ„طµط­ظٹط­ ===================
async def posting(user_id: int):
    """ظ†ط´ط± طھظ„ظ‚ط§ط¦ظٹ ظ…طھظ‚ط¯ظ… - ظٹط±ط³ظ„ ظ„ط¬ظ…ظٹط¹ ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ"""
    user_id_str = str(user_id)
    
    if not users.get(user_id_str, {}).get("posting"):
        return
    
    # طھط´ط؛ظٹظ„ ط¹ظ…ظٹظ„ ط§ظ„ظ…ط³طھط®ط¯ظ…
    client = Client(user_id_str, api_id=app.api_id, api_hash=app.api_hash, 
                    session_string=users[user_id_str]["session"])
    await client.start()
    
    try:
        while users[user_id_str].get("posting"):
            # ظ‚ط±ط§ط،ط© ط§ظ„ط¥ط¹ط¯ط§ط¯ط§طھ
            total_time = users[user_id_str].get("waitTime", 60)
            groups_data = users[user_id_str].get("groups", []).copy()
            captions_list = users[user_id_str].get("captions", []).copy()
            distribution_method = users[user_id_str].get("distribution_method", "random")
            
            # ط§ظ„طھط­ظ‚ظ‚ط§طھ
            if not captions_list:
                users[user_id_str]["posting"] = False
                write(users_db, users)
                await app.send_message(user_id, "â‌Œ طھظ… ط¥ظٹظ‚ط§ظپ ط§ظ„ظ†ط´ط±: ظ„ط§ طھظˆط¬ط¯ ظƒظ„ظٹط´ط§طھ")
                break
            
            if not groups_data:
                users[user_id_str]["posting"] = False
                write(users_db, users)
                await app.send_message(user_id, "â‌Œ طھظ… ط¥ظٹظ‚ط§ظپ ط§ظ„ظ†ط´ط±: ظ„ط§ طھظˆط¬ط¯ ظ…ط¬ظ…ظˆط¹ط§طھ")
                break
            
            num_groups = len(groups_data)
            await app.send_message(user_id, f"ًںڑ€ ط¨ط¯ط، ط¯ظˆط±ط© ظ†ط´ط± ط¬ط¯ظٹط¯ط©\nًں“ٹ ط¹ط¯ط¯ ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ: {num_groups}\nâڈ±ï¸ڈ ط§ظ„ظ…ط¯ط© ط§ظ„ط¥ط¬ظ…ط§ظ„ظٹط©: {total_time} ط«ط§ظ†ظٹط©")
            
            # ط®ظ„ط· ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ ط¹ط´ظˆط§ط¦ظٹط§ظ‹
            random.shuffle(groups_data)
            
            # ط­ط³ط§ط¨ ط§ظ„طھظˆط²ظٹط¹ ط§ظ„ط²ظ…ظ†ظٹ
            delays = calculate_distributed_delays(num_groups, total_time, distribution_method)
            
            # ط¥ظ†ط´ط§ط، ظ†ط³ط®ط© ظ…ظ† ط§ظ„ظƒظ„ظٹط´ط§طھ
            available_captions = captions_list.copy()
            
            # ط§ظ„ط¥ط±ط³ط§ظ„ ظ„ط¬ظ…ظٹط¹ ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ
            for idx, group_obj in enumerate(groups_data):
                if not users[user_id_str].get("posting"):
                    break
                
                group_id = group_obj["id"]
                invite_link = group_obj.get("link")
                
                # ط§ط®طھظٹط§ط± ظƒظ„ظٹط´ط© ط¹ط´ظˆط§ط¦ظٹط©
                if not available_captions:
                    available_captions = captions_list.copy()
                
                chosen_caption = random.choice(available_captions)
                available_captions.remove(chosen_caption)
                
                # ط¥ط±ط³ط§ظ„ ط§ظ„ط±ط³ط§ظ„ط©
                success = await send_to_group(client, user_id, group_id, chosen_caption, invite_link)
                
                if success:
                    await app.send_message(user_id, f"âœ… طھظ… ط§ظ„ط¥ط±ط³ط§ظ„ ط¥ظ„ظ‰ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© {idx+1}/{num_groups}")
                else:
                    await app.send_message(user_id, f"â‌Œ ظپط´ظ„ ط§ظ„ط¥ط±ط³ط§ظ„ ط¥ظ„ظ‰ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© {idx+1}/{num_groups}")
                
                # ط§ظ†طھط¸ط§ط± ط§ظ„ظپط±ظ‚ ط§ظ„ط²ظ…ظ†ظٹ ظ‚ط¨ظ„ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© ط§ظ„طھط§ظ„ظٹط© (ظˆظ„ظٹط³ ط¨ط¹ط¯ظ‡ط§)
                if idx < len(delays) - 1:
                    wait_time = delays[idx]
                    await app.send_message(user_id, f"âڈ³ ط§ظ†طھط¸ط§ط± {wait_time:.1f} ط«ط§ظ†ظٹط© ظ‚ط¨ظ„ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© ط§ظ„طھط§ظ„ظٹط©...")
                    await sleep(wait_time)
            
            # ط§ظ†طھط¸ط§ط± ط§ظ„ظ…ط¯ط© ط§ظ„ط¥ط¬ظ…ط§ظ„ظٹط© ظ‚ط¨ظ„ ط§ظ„ط¯ظˆط±ط© ط§ظ„طھط§ظ„ظٹط©
            await app.send_message(user_id, f"âڈ¸ï¸ڈ ط§ظƒطھظ…ظ„طھ ط§ظ„ط¯ظˆط±ط©طŒ ط§ظ†طھط¸ط§ط± {total_time} ط«ط§ظ†ظٹط© ظ‚ط¨ظ„ ط§ظ„ط¯ظˆط±ط© ط§ظ„طھط§ظ„ظٹط©...")
            await sleep(total_time)
            
    except Exception as e:
        print(f"ط®ط·ط£ ظپظٹ ط§ظ„ظ†ط´ط±: {e}")
        await app.send_message(user_id, f"âڑ ï¸ڈ ط­ط¯ط« ط®ط·ط£: {type(e).__name__}")
    finally:
        await client.stop()

# =================== ط£ظˆط§ظ…ط± ط§ظ„ظ…ط³طھط®ط¯ظ… ===================
@app.on_message(filters.command("start") & filters.private)
async def start(_: Client, message: Message):
    user_id = message.from_user.id
    
    # ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† ط§ظ„ط¥ط´طھط±ط§ظƒ
    subscribed = await subscription(message)
    if isinstance(subscribed, str):
        return await message.reply(f"âڑ ï¸ڈ ط¹ظ„ظٹظƒ ط§ظ„ط¥ط´طھط±ط§ظƒ ط¨ظ‚ظ†ط§ط© ط§ظ„ط¨ظˆطھ ط£ظˆظ„ط§ظ‹\nًں“¢ ط§ظ„ظ‚ظ†ط§ط©: @{subscribed}\nط§ط´طھط±ظƒ ط«ظ… ط§ط±ط³ظ„ /start")
    
    # ط¥ظ†ط´ط§ط، ط­ط³ط§ط¨ ط¬ط¯ظٹط¯
    if str(user_id) not in users:
        users[str(user_id)] = {
            "vip": True if user_id == owner else False,
            "smart_delay": True,
            "captions": [],
            "groups": [],
            "distribution_method": "random",
            "delete_after": 0,
            "waitTime": 60
        }
        write(users_db, users)
    
    # ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† ط§ظ„ظ€ VIP
    if user_id != owner and not users[str(user_id)].get("vip", False):
        return await message.reply(f"âڑ ï¸ڈ ظ„ط§ ظٹظ…ظƒظ†ظƒ ط§ط³طھط®ط¯ط§ظ… ظ‡ط°ط§ ط§ظ„ط¨ظˆطھ\nًں‘¤ طھظˆط§طµظ„ ظ…ط¹ [ط§ظ„ظ…ط·ظˆط±](tg://openmessage?user_id={owner}) ظ„طھظپط¹ظٹظ„ ط§ظ„ط¥ط´طھط±ط§ظƒ")
    
    fname = message.from_user.first_name
    caption = f"âœ¨ ظ…ط±ط­ط¨ط§ [{fname}](tg://settings)\nًں¤– ط¨ظˆطھ ط§ظ„ظ†ط´ط± ط§ظ„طھظ„ظ‚ط§ط¦ظٹ\nًں“‌ ط§ط³طھط®ط¯ظ… ط§ظ„ط£ط²ط±ط§ط± ظ„ظ„طھط­ظƒظ…:"
    await message.reply(caption, reply_markup=get_home_markup(user_id))

@app.on_callback_query(filters.regex(r"^(toHome)$"))
async def toHome(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    fname = callback.from_user.first_name
    caption = f"âœ¨ ظ…ط±ط­ط¨ط§ [{fname}](tg://settings)\nًں¤– ط¨ظˆطھ ط§ظ„ظ†ط´ط± ط§ظ„طھظ„ظ‚ط§ط¦ظٹ"
    await callback.message.edit_text(caption, reply_markup=get_home_markup(user_id))

# =================== ط¥ط¯ط§ط±ط© ط§ظ„ط­ط³ط§ط¨ ===================
@app.on_callback_query(filters.regex(r"^(account)$"))
async def account(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    has_session = users[str(user_id)].get("session") is not None
    status = "âœ… ظ…ط³ط¬ظ„" if has_session else "â‌Œ ط؛ظٹط± ظ…ط³ط¬ظ„"
    
    caption = f"ًں‘¤ **ط§ظ„ط­ط³ط§ط¨**\n\nط§ظ„ط­ط§ظ„ط©: {status}"
    markup = Markup([
        [Button("- طھط³ط¬ظٹظ„ ط­ط³ط§ط¨ -", callback_data="login")],
        [Button("- طھط؛ظٹظٹط± ط§ظ„ط­ط³ط§ط¨ -", callback_data="changeAccount")] if has_session else [],
        [Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="toHome")]
    ])
    await callback.message.edit_text(caption, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^(login|changeAccount)$"))
async def login(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="ًں“± ط£ط±ط³ظ„ ط±ظ‚ظ… ظ‡ط§طھظپظƒ ظ…ط¹ ط±ظ…ط² ط§ظ„ط¯ظˆظ„ط©\nظ…ط«ط§ظ„: +966512345678\n/cancel ظ„ظ„ط¥ظ„ط؛ط§ط،",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ", reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="account")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("âœ… طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،")
    
    await registration(ask)

async def registration(message: Message):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    msg = await message.reply("ًں”„ ط¬ط§ط±ظٹ طھط³ط¬ظٹظ„ ط§ظ„ط¯ط®ظˆظ„...")
    
    client = Client("temp", in_memory=True, api_id=app.api_id, api_hash=app.api_hash)
    await client.connect()
    
    try:
        sent_code = await client.send_code(phone)
    except PhoneNumberInvalid:
        return await msg.edit("â‌Œ ط±ظ‚ظ… ط§ظ„ظ‡ط§طھظپ ط؛ظٹط± طµط­ظٹط­")
    
    try:
        code = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="ًں”‘ طھظ… ط¥ط±ط³ط§ظ„ ط§ظ„ظƒظˆط¯. ط£ط±ط³ظ„ظ‡ ط§ظ„ط¢ظ†:",
            reply_markup=ForceReply(selective=True),
            timeout=120
        )
    except exceptions.TimeOut:
        return await msg.edit("âڈ° ط§ظ†طھظ‡ظ‰ ظˆظ‚طھ ط§ظ„ظƒظˆط¯")
    
    try:
        await client.sign_in(phone, sent_code.phone_code_hash, code.text)
    except SessionPasswordNeeded:
        try:
            password = await listener.listen(
                from_id=user_id, chat_id=user_id,
                text="ًں”’ ط­ط³ط§ط¨ظƒ ظ…ظپط¹ظ„ ط¨ط§ظ„طھط­ظ‚ظ‚ ط¨ط®ط·ظˆطھظٹظ†\nط£ط±ط³ظ„ ظƒظ„ظ…ط© ط§ظ„ظ…ط±ظˆط±:",
                reply_markup=ForceReply(selective=True),
                timeout=60
            )
        except exceptions.TimeOut:
            return await msg.edit("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ")
        await client.check_password(password.text)
    
    session = await client.export_session_string()
    await client.disconnect()
    
    users[str(user_id)]["session"] = session
    write(users_db, users)
    
    await app.send_message(user_id, "âœ… طھظ… طھط³ط¬ظٹظ„ ط§ظ„ط¯ط®ظˆظ„ ط¨ظ†ط¬ط§ط­", 
                          reply_markup=Markup([[Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")]]))

# =================== ط¥ط¯ط§ط±ط© ط§ظ„ط³ظˆط¨ط±ط§طھ ===================
@app.on_callback_query(filters.regex(r"^(newSuper)$"))
async def newSuper(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="â‍• ط£ط±ط³ظ„ ط±ط§ط¨ط· ط£ظˆ ظ…ط¹ط±ظپ ط§ظ„ظ…ط¬ظ…ظˆط¹ط©\nظ…ط«ط§ظ„: @username ط£ظˆ https://t.me/username\n/cancel ظ„ظ„ط¥ظ„ط؛ط§ط،",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ", reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="toHome")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("âœ… طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،")
    
    input_text = ask.text.strip()
    group_id = None
    invite_link = None
    
    # ظ…ط¹ط§ظ„ط¬ط© ط§ظ„ظ…ط¹ط±ظپ
    if input_text.startswith("@"):
        username = input_text[1:]
        try:
            chat = await app.get_chat(username)
            group_id = chat.id
            invite_link = input_text
        except:
            return await ask.reply("â‌Œ ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط§ظ„ظ…ط¬ظ…ظˆط¹ط©")
    
    # ظ…ط¹ط§ظ„ط¬ط© ط§ظ„ط±ط§ط¨ط·
    elif "t.me/" in input_text:
        username = input_text.split("t.me/")[-1]
        try:
            chat = await app.get_chat(username)
            group_id = chat.id
            invite_link = input_text
        except:
            return await ask.reply("â‌Œ ط±ط§ط¨ط· ط؛ظٹط± طµط§ظ„ط­")
    
    # ظ…ط¹ط§ظ„ط¬ط© ط§ظ„ط£ظٹط¯ظٹ
    elif input_text.lstrip("-").isdigit():
        group_id = int(input_text)
    
    else:
        return await ask.reply("â‌Œ طµظٹط؛ط© ط؛ظٹط± طµط§ظ„ط­ط©")
    
    if group_id:
        if "groups" not in users[str(user_id)]:
            users[str(user_id)]["groups"] = []
        
        # ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† ط¹ط¯ظ… ط§ظ„طھظƒط±ط§ط±
        existing = [g for g in users[str(user_id)]["groups"] if g["id"] == group_id]
        if existing:
            return await ask.reply("âڑ ï¸ڈ ظ‡ط°ظ‡ ط§ظ„ظ…ط¬ظ…ظˆط¹ط© ظ…ظˆط¬ظˆط¯ط© ط¨ط§ظ„ظپط¹ظ„")
        
        users[str(user_id)]["groups"].append({"id": group_id, "link": invite_link})
        write(users_db, users)
        
        try:
            chat = await app.get_chat(group_id)
            title = chat.title
        except:
            title = str(group_id)
        
        await ask.reply(f"âœ… طھظ… ط¥ط¶ط§ظپط© ط§ظ„ظ…ط¬ظ…ظˆط¹ط©: {title}\nًں“ٹ ط§ظ„ط¹ط¯ط¯ ط§ظ„ط­ط§ظ„ظٹ: {len(users[str(user_id)]['groups'])}",
                       reply_markup=Markup([[Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")]]))

@app.on_callback_query(filters.regex(r"^(currentSupers)$"))
async def currentSupers(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    groups = users[str(user_id)].get("groups", [])
    
    if not groups:
        return await callback.answer("ًں“­ ظ„ط§ طھظˆط¬ط¯ ظ…ط¬ظ…ظˆط¹ط§طھ", show_alert=True)
    
    markup = []
    for g in groups:
        try:
            chat = await app.get_chat(g["id"])
            title = chat.title[:25]
        except:
            title = str(g["id"])[:25]
        markup.append([Button(f"ًں“¢ {title}", callback_data=f"super_{g['id']}"), 
                      Button("ًں—‘ï¸ڈ", callback_data=f"delSuper_{g['id']}")])
    
    markup.append([Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")])
    await callback.message.edit_text(f"ًں“‹ **ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ ({len(groups)})**:", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^delSuper_"))
async def delSuper(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    gid = int(callback.data.split("_")[1])
    
    groups = users[str(user_id)].get("groups", [])
    users[str(user_id)]["groups"] = [g for g in groups if g["id"] != gid]
    write(users_db, users)
    
    await callback.answer("âœ… طھظ… ط§ظ„ط­ط°ظپ", show_alert=True)
    await currentSupers(_, callback)

# =================== ط¥ط¯ط§ط±ط© ط§ظ„ظƒظ„ظٹط´ط§طھ ===================
@app.on_callback_query(filters.regex(r"^(manageCaptions)$"))
async def manageCaptions(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    captions = users[str(user_id)].get("captions", [])
    
    markup = []
    for idx, cap in enumerate(captions):
        short = cap[:20] + "..." if len(cap) > 20 else cap
        markup.append([Button(f"ًں“‌ {short}", callback_data=f"viewCap_{idx}"), 
                      Button("ًں—‘ï¸ڈ", callback_data=f"delCap_{idx}")])
    
    markup.append([Button("â‍• ط¥ط¶ط§ظپط© ظƒظ„ظٹط´ط©", callback_data="addCaption")])
    markup.append([Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")])
    
    count = len(captions)
    if count == 0:
        await callback.message.edit_text("ًں“­ **ظ„ط§ طھظˆط¬ط¯ ظƒظ„ظٹط´ط§طھ**\nâ‍• ط£ط¶ظپ ظƒظ„ظٹط´ط© ط¬ط¯ظٹط¯ط©:", reply_markup=Markup(markup))
    else:
        await callback.message.edit_text(f"ًں“‌ **ط§ظ„ظƒظ„ظٹط´ط§طھ ({count})**:", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^(addCaption)$"))
async def addCaption(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text="ًں“‌ ط£ط±ط³ظ„ ظ†طµ ط§ظ„ظƒظ„ظٹط´ط© ط§ظ„ط¬ط¯ظٹط¯ط©\n/cancel ظ„ظ„ط¥ظ„ط؛ط§ط،",
            reply_markup=ForceReply(selective=True),
            timeout=120
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ", reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="manageCaptions")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("âœ… طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،")
    
    captions = users[str(user_id)].get("captions", [])
    captions.append(ask.text)
    users[str(user_id)]["captions"] = captions
    write(users_db, users)
    
    await ask.reply(f"âœ… طھظ… ط¥ط¶ط§ظپط© ط§ظ„ظƒظ„ظٹط´ط©\nًں“ٹ ط§ظ„ط¹ط¯ط¯ ط§ظ„ط­ط§ظ„ظٹ: {len(captions)}",
                   reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="manageCaptions")]]))

@app.on_callback_query(filters.regex(r"^delCap_"))
async def delCaption(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    idx = int(callback.data.split("_")[1])
    
    captions = users[str(user_id)].get("captions", [])
    if 0 <= idx < len(captions):
        captions.pop(idx)
        users[str(user_id)]["captions"] = captions
        write(users_db, users)
        await callback.answer("âœ… طھظ… ط§ظ„ط­ط°ظپ", show_alert=True)
    
    await manageCaptions(_, callback)

@app.on_callback_query(filters.regex(r"^viewCap_"))
async def viewCaption(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    idx = int(callback.data.split("_")[1])
    
    captions = users[str(user_id)].get("captions", [])
    if 0 <= idx < len(captions):
        await callback.answer("ًں“„ ظ…ط¹ط§ظٹظ†ط©:", show_alert=True)
        await callback.message.reply(f"**ظ†طµ ط§ظ„ظƒظ„ظٹط´ط©:**\n{captions[idx]}", 
                                    reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="manageCaptions")]]))

# =================== ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ†ط´ط± ===================
@app.on_callback_query(filters.regex(r"^(waitTime)$"))
async def waitTime(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("waitTime", 60)
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text=f"âڈ±ï¸ڈ **ط§ظ„ظ…ط¯ط© ط§ظ„ط­ط§ظ„ظٹط©:** {current} ط«ط§ظ†ظٹط©\n\nط£ط±ط³ظ„ ط§ظ„ظ…ط¯ط© ط§ظ„ط¬ط¯ظٹط¯ط© (ط¨ط§ظ„ط«ظˆط§ظ†ظٹ)\nط§ظ„ط­ط¯ ط§ظ„ط£ط¯ظ†ظ‰: 10 ط«ظˆط§ظ†ظچ\n/cancel ظ„ظ„ط¥ظ„ط؛ط§ط،",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ", reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="toHome")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("âœ… طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،")
    
    try:
        wait = int(ask.text)
        if wait < 10:
            return await ask.reply("âڑ ï¸ڈ ط§ظ„ظ…ط¯ط© ظٹط¬ط¨ ط£ظ† طھظƒظˆظ† 10 ط«ظˆط§ظ†ظچ ط¹ظ„ظ‰ ط§ظ„ط£ظ‚ظ„")
        users[str(user_id)]["waitTime"] = wait
        write(users_db, users)
        await ask.reply(f"âœ… طھظ… طھط¹ظٹظٹظ† ط§ظ„ظ…ط¯ط©: {wait} ط«ط§ظ†ظٹط©", 
                       reply_markup=Markup([[Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")]]))
    except ValueError:
        await ask.reply("â‌Œ ط£ط±ط³ظ„ ط±ظ‚ظ…ط§ظ‹ طµط­ظٹط­ط§ظ‹")

@app.on_callback_query(filters.regex(r"^(deleteTime)$"))
async def deleteTime(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("delete_after", 0)
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=user_id, chat_id=user_id,
            text=f"ًں—‘ï¸ڈ **ظ…ط¯ط© ط§ظ„ط­ط°ظپ ط§ظ„ط­ط§ظ„ظٹط©:** {current if current > 0 else 'ظ…ط¹ط·ظ„'}\n\nط£ط±ط³ظ„ ط§ظ„ظ…ط¯ط© ط§ظ„ط¬ط¯ظٹط¯ط© (ط¨ط§ظ„ط«ظˆط§ظ†ظٹ)\n0 = طھط¹ط·ظٹظ„ ط§ظ„ط­ط°ظپ\n/cancel ظ„ظ„ط¥ظ„ط؛ط§ط،",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ", reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="toHome")]]))
    
    if ask.text == "/cancel":
        return await ask.reply("âœ… طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،")
    
    try:
        delete_after = int(ask.text)
        if delete_after < 0:
            return await ask.reply("âڑ ï¸ڈ ط£ط¯ط®ظ„ ظ‚ظٹظ…ط© 0 ط£ظˆ ط£ظƒط«ط±")
        users[str(user_id)]["delete_after"] = delete_after
        write(users_db, users)
        status = "ظ…ط¹ط·ظ„" if delete_after == 0 else f"{delete_after} ط«ط§ظ†ظٹط©"
        await ask.reply(f"âœ… طھظ… طھط¹ظٹظٹظ† ظ…ط¯ط© ط§ظ„ط­ط°ظپ: {status}", 
                       reply_markup=Markup([[Button("- ط§ظ„ط±ط¦ظٹط³ظٹظ‡ -", callback_data="toHome")]]))
    except ValueError:
        await ask.reply("â‌Œ ط£ط±ط³ظ„ ط±ظ‚ظ…ط§ظ‹ طµط­ظٹط­ط§ظ‹")

@app.on_callback_query(filters.regex(r"^(distributionMethod)$"))
async def distributionMethod(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text("ًں“ٹ **ط§ط®طھط± ط·ط±ظٹظ‚ط© طھظˆط²ظٹط¹ ط§ظ„ظپط±ظˆظ‚ ط§ظ„ط²ظ…ظ†ظٹط©:**", 
                                    reply_markup=get_distribution_markup(user_id))

@app.on_callback_query(filters.regex(r"^setDist_"))
async def setDistribution(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    method = callback.data.split("_")[1]
    
    users[str(user_id)]["distribution_method"] = method
    write(users_db, users)
    
    method_names = {"equal": "ط§ظ„ظ…طھط³ط§ظˆظٹ", "random": "ط§ظ„ط¹ط´ظˆط§ط¦ظٹ", "fibonacci": "ظپظٹط¨ظˆظ†ط§طھط´ظٹ"}
    await callback.answer(f"âœ… طھظ… طھط¹ظٹظٹظ† ط·ط±ظٹظ‚ط© {method_names[method]}", show_alert=True)
    await distributionMethod(_, callback)

@app.on_callback_query(filters.regex(r"^(toggleSmartDelay)$"))
async def toggleSmartDelay(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    current = users[str(user_id)].get("smart_delay", True)
    users[str(user_id)]["smart_delay"] = not current
    write(users_db, users)
    await callback.answer(f"âœ… طھظ… {'طھظپط¹ظٹظ„' if not current else 'طھط¹ط·ظٹظ„'} ط§ظ„طھط£ط®ظٹط± ط§ظ„ط°ظƒظٹ", show_alert=True)
    await toHome(_, callback)

# =================== ط¨ط¯ط، ظˆط¥ظٹظ‚ط§ظپ ط§ظ„ظ†ط´ط± ===================
@app.on_callback_query(filters.regex(r"^(startPosting)$"))
async def startPosting(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if not users[str(user_id)].get("session"):
        return await callback.answer("â‌Œ ظٹط¬ط¨ طھط³ط¬ظٹظ„ ط­ط³ط§ط¨ ط£ظˆظ„ط§ظ‹", show_alert=True)
    
    if not users[str(user_id)].get("groups"):
        return await callback.answer("â‌Œ ظٹط¬ط¨ ط¥ط¶ط§ظپط© ظ…ط¬ظ…ظˆط¹ط§طھ ط£ظˆظ„ط§ظ‹", show_alert=True)
    
    if not users[str(user_id)].get("captions"):
        return await callback.answer("â‌Œ ظٹط¬ط¨ ط¥ط¶ط§ظپط© ظƒظ„ظٹط´ط§طھ ط£ظˆظ„ط§ظ‹", show_alert=True)
    
    if users[str(user_id)].get("posting"):
        return await callback.answer("âڑ ï¸ڈ ط§ظ„ظ†ط´ط± ظ…ظپط¹ظ„ ط¨ط§ظ„ظپط¹ظ„", show_alert=True)
    
    users[str(user_id)]["posting"] = True
    write(users_db, users)
    
    task = create_task(posting(user_id))
    active_tasks.add(str(user_id))
    task.add_done_callback(lambda t: active_tasks.discard(str(user_id)))
    
    groups_count = len(users[str(user_id)]["groups"])
    captions_count = len(users[str(user_id)]["captions"])
    wait_time = users[str(user_id)].get("waitTime", 60)
    
    await callback.message.edit_text(
        f"ًںڑ€ **ط¨ط¯ط، ط§ظ„ظ†ط´ط± ط§ظ„طھظ„ظ‚ط§ط¦ظٹ**\n\n"
        f"ًں“ٹ ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ: {groups_count}\n"
        f"ًں“‌ ط§ظ„ظƒظ„ظٹط´ط§طھ: {captions_count}\n"
        f"âڈ±ï¸ڈ ط§ظ„ظ…ط¯ط©: {wait_time} ط«ط§ظ†ظٹط©\n\n"
        f"âœ… ط³ظٹطھظ… ط§ظ„ط¥ط±ط³ط§ظ„ ظ„ط¬ظ…ظٹط¹ ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ",
        reply_markup=Markup([[Button("âڈ¹ï¸ڈ ط¥ظٹظ‚ط§ظپ", callback_data="stopPosting"), 
                             Button("ًںڈ  ط§ظ„ط±ط¦ظٹط³ظٹظ‡", callback_data="toHome")]])
    )

@app.on_callback_query(filters.regex(r"^(stopPosting)$"))
async def stopPosting(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if not users[str(user_id)].get("posting"):
        return await callback.answer("âڑ ï¸ڈ ط§ظ„ظ†ط´ط± ظ…ط¹ط·ظ„ ط¨ط§ظ„ظپط¹ظ„", show_alert=True)
    
    users[str(user_id)]["posting"] = False
    write(users_db, users)
    
    await callback.message.edit_text("ًں›‘ **طھظ… ط¥ظٹظ‚ط§ظپ ط§ظ„ظ†ط´ط± ط§ظ„طھظ„ظ‚ط§ط¦ظٹ**", 
                                    reply_markup=Markup([[Button("â–¶ï¸ڈ ط¨ط¯ط،", callback_data="startPosting"), 
                                                         Button("ًںڈ  ط§ظ„ط±ط¦ظٹط³ظٹظ‡", callback_data="toHome")]]))

# =================== ظ‚ط³ظ… ط§ظ„ظ…ط§ظ„ظƒ ===================
async def isOwner(_, __, message: Message) -> bool:
    return message.from_user.id == owner

owner_filter = filters.create(isOwner)

@app.on_message(filters.command("admin") & filters.private & owner_filter)
async def adminPanel(_: Client, message: Message):
    await message.reply("ًں‘‘ **ظ„ظˆط­ط© طھط­ظƒظ… ط§ظ„ظ…ط§ظ„ظƒ**", reply_markup=Markup([
        [Button("â‍• طھظپط¹ظٹظ„ VIP", callback_data="addVIP"), Button("â‍– ط§ظ„ط؛ط§ط، VIP", callback_data="cancelVIP")],
        [Button("ًں“ٹ ط§ظ„ط§ط­طµط§ط¦ظٹط§طھ", callback_data="statics"), Button("ًں“¢ ظ‚ظ†ظˆط§طھ ط§ظ„ط¥ط´طھط±ط§ظƒ", callback_data="channels")],
        [Button("ًں›،ï¸ڈ ط­ظ…ط§ظٹط© ط§ظ„ط®طµظˆطµظٹط©", callback_data="privacyProtection")]
    ]))

@app.on_callback_query(filters.regex("addVIP") & owner_filter)
async def addVIP(_: Client, callback: CallbackQuery):
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=owner, chat_id=owner,
            text="ًں‘¤ ط£ط±ط³ظ„ ط§ظٹط¯ظٹ ط§ظ„ظ…ط³طھط®ط¯ظ…",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ")
    
    try:
        user_id = int(ask.text)
    except:
        return await ask.reply("â‌Œ ط§ظٹط¯ظٹ ط؛ظٹط± طµط§ظ„ط­")
    
    try:
        days = await listener.listen(
            from_id=owner, chat_id=owner,
            text="ًں“… ط£ط±ط³ظ„ ط¹ط¯ط¯ ط§ظ„ط£ظٹط§ظ…",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ")
    
    try:
        limit_days = int(days.text)
    except:
        return await days.reply("â‌Œ ط£ط±ط³ظ„ ط±ظ‚ظ…ط§ظ‹ طµط­ظٹط­ط§ظ‹")
    
    if str(user_id) not in users:
        users[str(user_id)] = {"vip": True, "smart_delay": True, "captions": [], "groups": [], "waitTime": 60}
    else:
        users[str(user_id)]["vip"] = True
    
    end_date = datetime.now(_timezone) + timedelta(days=limit_days)
    users[str(user_id)]["limitation"] = {
        "days": limit_days,
        "endDate": end_date.strftime("%Y-%m-%d"),
        "endTime": end_date.strftime("%H:%M")
    }
    write(users_db, users)
    
    await days.reply(f"âœ… طھظ… طھظپط¹ظٹظ„ VIP ظ„ظ„ظ…ط³طھط®ط¯ظ… {user_id}\nًں“… ط§ظ„ظ…ط¯ط©: {limit_days} ظٹظˆظ…",
                    reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="admin")]]))

@app.on_callback_query(filters.regex("cancelVIP") & owner_filter)
async def cancelVIP(_: Client, callback: CallbackQuery):
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=owner, chat_id=owner,
            text="ًں‘¤ ط£ط±ط³ظ„ ط§ظٹط¯ظٹ ط§ظ„ظ…ط³طھط®ط¯ظ…",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ")
    
    user_id = ask.text
    if user_id in users:
        users[user_id]["vip"] = False
        write(users_db, users)
        await ask.reply(f"âœ… طھظ… ط§ظ„ط؛ط§ط، VIP ظ„ظ„ظ…ط³طھط®ط¯ظ… {user_id}",
                       reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="admin")]]))
    else:
        await ask.reply("â‌Œ ط§ظ„ظ…ط³طھط®ط¯ظ… ط؛ظٹط± ظ…ظˆط¬ظˆط¯")

@app.on_callback_query(filters.regex("statics") & owner_filter)
async def statics(_: Client, callback: CallbackQuery):
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip", False))
    posting = sum(1 for u in users.values() if u.get("posting", False))
    total_groups = sum(len(u.get("groups", [])) for u in users.values())
    total_captions = sum(len(u.get("captions", [])) for u in users.values())
    
    await callback.message.edit_text(
        f"ًں“ٹ **ط§ظ„ط¥ط­طµط§ط¦ظٹط§طھ**\n\n"
        f"ًں‘¥ ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ظ…ط³طھط®ط¯ظ…ظٹظ†: {total}\n"
        f"â­گ ظ…ط³طھط®ط¯ظ…ظٹ VIP: {vip}\n"
        f"ًںڑ€ ط§ظ„ظ†ط´ط± ظ…ظپط¹ظ„: {posting}\n"
        f"ًں“¢ ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ظ…ط¬ظ…ظˆط¹ط§طھ: {total_groups}\n"
        f"ًں“‌ ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ظƒظ„ظٹط´ط§طھ: {total_captions}",
        reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="admin")]])
    )

@app.on_callback_query(filters.regex("channels") & owner_filter)
async def channelsControl(_: Client, callback: CallbackQuery):
    markup = []
    for ch in channels:
        markup.append([Button(f"ًں“¢ @{ch}", url=f"https://t.me/{ch}"), 
                      Button("ًں—‘ï¸ڈ", callback_data=f"removeChannel_{ch}")])
    markup.append([Button("â‍• ط¥ط¶ط§ظپط© ظ‚ظ†ط§ط©", callback_data="addChannel")])
    markup.append([Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="admin")])
    
    await callback.message.edit_text("ًں“¢ **ظ‚ظ†ظˆط§طھ ط§ظ„ط¥ط´طھط±ط§ظƒ ط§ظ„ط¥ط¬ط¨ط§ط±ظٹ**", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex("addChannel") & owner_filter)
async def addChannel(_: Client, callback: CallbackQuery):
    await callback.message.delete()
    
    try:
        ask = await listener.listen(
            from_id=owner, chat_id=owner,
            text="ًں“¢ ط£ط±ط³ظ„ ظ…ط¹ط±ظپ ط§ظ„ظ‚ظ†ط§ط© (ط¨ط¯ظˆظ† @)\nظ…ط«ط§ظ„: channelusername",
            reply_markup=ForceReply(selective=True),
            timeout=30
        )
    except exceptions.TimeOut:
        return await callback.message.reply("âڈ° ط§ظ†طھظ‡ظ‰ ط§ظ„ظˆظ‚طھ")
    
    channel = ask.text.strip()
    channels.append(channel)
    write(channels_db, channels)
    
    await ask.reply(f"âœ… طھظ… ط¥ط¶ط§ظپط© ظ‚ظ†ط§ط© @{channel}",
                   reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="channels")]]))

@app.on_callback_query(filters.regex("removeChannel_") & owner_filter)
async def removeChannel(_: Client, callback: CallbackQuery):
    channel = callback.data.split("_")[1]
    if channel in channels:
        channels.remove(channel)
        write(channels_db, channels)
        await callback.answer("âœ… طھظ… ط§ظ„ط­ط°ظپ", show_alert=True)
    await channelsControl(_, callback)

@app.on_callback_query(filters.regex("privacyProtection") & owner_filter)
async def privacyProtection(_: Client, callback: CallbackQuery):
    global privacy_protection_active
    privacy_protection_active = not privacy_protection_active
    
    status = "ظ…ظپط¹ظ„ط© âœ…" if privacy_protection_active else "ظ…ط¹ط·ظ„ط© â‌Œ"
    await callback.answer(f"ط­ظ…ط§ظٹط© ط§ظ„ط®طµظˆطµظٹط© {status}", show_alert=True)
    await callback.message.edit_text(
        f"ًں›،ï¸ڈ **ط­ظ…ط§ظٹط© ط³ظٹط§ط³ط© ط§ظ„ط®طµظˆطµظٹط©**\n\n"
        f"ط§ظ„ط­ط§ظ„ط©: {status}\n\n"
        f"ط¹ظ†ط¯ ط§ظ„طھظپط¹ظٹظ„طŒ ظٹظ‚ظˆظ… ط§ظ„ط¨ظˆطھ ط¨ط§ظ„ط±ط¯ طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ط¹ظ„ظ‰ ط£ط³ط¦ظ„ط© ط¨ظˆطھط§طھ ط§ظ„ط®طµظˆطµظٹط©\n"
        f"ط¨ط¥ط¬ط§ط¨ط§طھ ط¹ط´ظˆط§ط¦ظٹط© طھط­ط§ظƒظٹ ط§ظ„ظ…ط³طھط®ط¯ظ…ظٹظ† ط§ظ„ط­ظ‚ظٹظ‚ظٹظٹظ†.",
        reply_markup=Markup([[Button("- ط§ظ„ط¹ظˆط¯ظ‡ -", callback_data="admin")]])
    )

# =================== ط§ظ„ط¥ط´طھط±ط§ظƒ ط§ظ„ط¥ط¬ط¨ط§ط±ظٹ ===================
async def subscription(message: Message) -> Union[bool, str]:
    user_id = message.from_user.id
    for channel in channels:
        try:
            await app.get_chat_member(channel, user_id)
        except UserNotParticipant:
            return channel
    return True

# =================== ط¥ط¯ط§ط±ط© ط§ظ„طھط®ط²ظٹظ† ===================
def write(file_path: str, data: Any):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read(file_path: str) -> Any:
    if not os.path.exists(file_path):
        write(file_path, {} if "users" in file_path else [])
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# =================== ط¯ظˆط§ظ„ ط¥ط¹ط§ط¯ط© ط§ظ„طھط´ط؛ظٹظ„ ===================
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
                        await app.send_message(int(user_id), "âڑ ï¸ڈ ط§ظ†طھظ‡طھ طµظ„ط§ط­ظٹط© ط§ظ„ط§ط´طھط±ط§ظƒ VIP")
                    except:
                        pass
        await sleep(3600)

# =================== ط§ظ„طھط´ط؛ظٹظ„ ط§ظ„ط±ط¦ظٹط³ظٹ ===================
_timezone = timezone("Asia/Baghdad")
users_db = "users.json"
channels_db = "channels.json"
users = read(users_db)
channels = read(channels_db)

async def main():
    print("ًں¤– طھط´ط؛ظٹظ„ ط§ظ„ط¨ظˆطھ...")
    create_task(restartPosting())
    create_task(checkVIPExpiry())
    await app.start()
    print("âœ… ط§ظ„ط¨ظˆطھ ظٹط¹ظ…ظ„ ط¨ظ†ط¬ط§ط­!")
    print(f"ًں‘‘ ط§ظ„ظ…ط·ظˆط±: {owner}")
    print(f"ًں“ٹ ط§ظ„ظ…ط³طھط®ط¯ظ…ظٹظ†: {len(users)}")
    await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
