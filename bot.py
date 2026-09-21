# bot.py - Short Drama Video Agent v1.1 Patch
# FIXES: BOT_TOKEN env only + Evidence Gate + Edit Operation Log + Versioning
# SCOPE LOCK: No Visual Factory, No Monetization Backend change, No real Publisher APIs

import asyncio, json, os, uuid
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# === 1. BOT_TOKEN - ENV ONLY - FAIL FAST IF ABSENT ===
def get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token or token.strip() == "":
        raise RuntimeError(
            "BOT_TOKEN is missing. Set BOT_TOKEN in environment. "
            "See .env.example: BOT_TOKEN= . "
            "No token may exist in source code."
        )
    # Basic sanity: telegram bot tokens are like 123456:ABC...
    if ":" not in token or len(token) < 20:
        raise RuntimeError("BOT_TOKEN format invalid - expected format like 123456789:ABC... - check env")
    return token

# Load trending stories
with open(os.path.join(os.path.dirname(__file__), "trending_stories.json"), "r", encoding="utf-8") as f:
    TRENDING = json.load(f)

# === 3. EDIT OPERATION LOG + VERSIONING - v1.2 with persistence abstraction ===
# In-memory cache + DB source of truth
video_versions: Dict[str, Dict] = {}
operation_logs: List[Dict] = []

# Persistence integration - lazy init
_persistence_repo = None

def get_persistence():
    global _persistence_repo
    if _persistence_repo is None:
        try:
            from persistence.repository import get_repository
            _persistence_repo = get_repository()
            _persistence_repo.init_schema()
        except Exception as e:
            print(f"Warning: persistence init failed in bot.py: {e} - falling back to in-memory")
            _persistence_repo = None
    return _persistence_repo


def create_operation_log(
    user_id: str,
    video_id: str,
    operation_type: str,
    parsed_value: Optional[str] = None,
    generated_prompt: Optional[str] = None,
    parent_version: Optional[str] = None
) -> Dict:
    """Every edit generates operation_id + version increment v1→v2→v3"""
    op_id = f"op_{uuid.uuid4().hex[:12]}"
    
    # Determine versioning
    if video_id not in video_versions:
        video_versions[video_id] = {"current_version": "v1", "history": []}
        parent = None
        new_version = "v1"
    else:
        current = video_versions[video_id]["current_version"]
        # Parse v number
        try:
            num = int(current[1:])
        except:
            num = 1
        parent = current
        new_version = f"v{num+1}"
    
    # Override parent if explicitly provided
    if parent_version:
        parent = parent_version
    
    log = {
        "operation_id": op_id,
        "user_id": str(user_id),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "video_id": video_id,
        "parent_version": parent,
        "new_version": new_version,
        "operation_type": operation_type,
        "parsed_value": parsed_value,
        "generated_prompt": generated_prompt,
        "preview_reference": f"{video_id}_{new_version}_preview.mp4",
        "status": "PENDING_PREVIEW"
    }
    
    operation_logs.append(log)
    
    # Update in-memory cache
    video_versions[video_id]["current_version"] = new_version
    video_versions[video_id]["history"].append(log)
    
    # Persist to DB - source of truth
    try:
        repo = get_persistence()
        if repo:
            repo.create_operation_log(log)
            repo.create_or_update_video_version(video_id, new_version)
    except Exception as e:
        print(f"Warning: failed to persist operation log: {e}")
    
    return log

def get_video_version_info(video_id: str) -> Dict:
    # Check DB first for persistence across restarts
    try:
        repo = get_persistence()
        if repo:
            db_version = repo.get_video_version(video_id)
            if db_version:
                history = repo.list_operation_history(video_id)
                return {"current_version": db_version["current_version"], "history": history}
    except Exception as e:
        print(f"Warning: failed to get video version from DB: {e}")
    return video_versions.get(video_id, {"current_version": None, "history": []})

# Edit understanding - Arabic comments parser (preserved from v1)
EDIT_KEYWORDS = {
    "اضاءة": "lighting",
    "اغمق": "darker", "افتح": "brighter",
    "قص": "cut", "اقطع": "trim",
    "كابشن": "caption", "عنوان": "title",
    "موسيقى": "music", "صوت": "sound",
    "اسرع": "faster", "ابطأ": "slower",
    "اضافة": "add", "احذف": "delete",
    "طويل": "longer", "قصير": "shorter",
    "الوان": "colors", "فلتر": "filter",
    "خلفية": "background", "زوم": "zoom"
}

def parse_edit_comment(text: str):
    """يفهم تعليقاتك بالعربي وينفذها - preserved"""
    text_lower = text.lower()
    actions = []
    for ar, en in EDIT_KEYWORDS.items():
        if ar in text_lower:
            actions.append(en)
    
    result = {
        "raw": text,
        "actions": actions,
        "understood": len(actions) > 0,
        "operations": []
    }
    
    if "اغمق" in text_lower or "اضاءة" in text_lower:
        result["operations"].append({"type": "lighting", "value": "darker", "prompt": "dramatic low-key lighting, darker shadows, cinematic"})
    if "افتح" in text_lower:
        result["operations"].append({"type": "lighting", "value": "brighter", "prompt": "brighter, high-key lighting"})
    if "قص" in text_lower or "اقطع" in text_lower:
        import re
        secs = re.findall(r'(\d+)\s*ث', text_lower)
        result["operations"].append({"type": "trim", "seconds": secs[0] if secs else "3", "prompt": f"trim first {secs[0] if secs else 3} seconds"})
    if "كابشن" in text_lower or "عنوان" in text_lower:
        result["operations"].append({"type": "caption", "new_text": text, "prompt": "regenerate caption"})
    if "اسرع" in text_lower:
        result["operations"].append({"type": "speed", "value": "1.25x"})
    if "ابطأ" in text_lower:
        result["operations"].append({"type": "speed", "value": "0.85x"})
    
    return result

# === HANDLERS (Telegram approval gate preserved) ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 الأكثر ربحاً الآن", callback_data="show_trending")],
        [InlineKeyboardButton("📝 ابعت قصتك", callback_data="send_story")],
        [InlineKeyboardButton("📊 أرباحي", callback_data="my_earnings")]
    ]
    await update.message.reply_text(
        "🎬 **Short Drama Video Agent v1.1**\n\n"
        "أنا بعمل:\n"
        "1. سكان للقصص التريندج المربحة\n"
        "2. تقطيع القصة لـ 5-7 حلقات 9:16\n"
        "3. توليد فيديوهات بنفس الشخصيات\n"
        "4. بفهم تعليقاتك وبعدل (مع versioning)\n"
        "5. نشر بعد Approve فقط + Evidence Gate\n"
        "6. لا Royalty إلا بـ receipt حقيقي\n\n"
        "اختار:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not TRENDING:
        await query.edit_message_text(
            "🔎 مفيش Trend data live متاحة حالياً.\n\n"
            "الـagent مش هيعرض بيانات views/profit ثابتة أو قديمة على إنها تريند حالي.\n"
            "لازم YouTube Data API أو TikTok Research API يكون متاح قبل تشغيل Live Discovery.",
            parse_mode="Markdown"
        )
        return

    text = "🔥 **Live Trend Observations**\n\n"
    keyboard = []
    for i, story in enumerate(TRENDING[:5]):
        text += f"{i+1}. **{story['title']}**\n"
        text += f"   Evidence: {story.get('evidence_status','UNKNOWN')}\n"
        text += f"   Source: {story.get('source','unknown')}\n"
        text += f"   Observed: {story.get('observed_at','UNKNOWN')}\n\n"
        keyboard.append([InlineKeyboardButton(f"اختار {story['title'][:20]}", callback_data=f"select_{story['id']}")])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_home")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    story_id = query.data.replace("select_", "")
    story = next((s for s in TRENDING if s["id"] == story_id), None)
    if not story:
        return
    
    context.user_data["selected_story"] = story
    context.user_data["selected_story_id"] = story_id
    
    keyboard = [
        [InlineKeyboardButton("🎬 جهز خطة الحلقات", callback_data=f"generate_{story_id}")],
        [InlineKeyboardButton("🔙 رجوع للتريندج", callback_data="show_trending")]
    ]
    
    await query.edit_message_text(
        f"✅ اخترت: **{story['title']}**\n\n"
        f"📖 القصة: {story['story_outline']}\n\n"
        f"🎬 هيتقطع لـ {story['beats']} حلقات\n"
        f"💰 متوسط الربح: {story['avg_episode_cost']} [CONFIG]\n"
        f"🏷️ Tags: {', '.join(story['tags'])}\n\n"
        f"أبدأ التوليد ولا عايز تعدل حاجة؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    story_id = query.data.replace("generate_", "")
    story = next((s for s in TRENDING if s["id"] == story_id), None)
    if not story:
        await query.edit_message_text("القصة غير موجودة في مصدر Live Discovery.")
        return

    await query.edit_message_text(
        f"🧩 **خطة إنتاج فقط — {story['title']}**\n\n"
        f"الحلقات المخططة: {story.get('beats', 0)}\n"
        "الحالة: PLAN_ONLY\n"
        "Generation evidence: NOT_AVAILABLE\n"
        "لا يوجد Preview أو Publish أو Approve قبل ظهور artifact حقيقي.",
        parse_mode="Markdown"
    )

async def handle_edit_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)
    video_id = context.user_data.get("last_video_id", "generic_video")

    parsed = parse_edit_comment(text)
    if not parsed["understood"]:
        await update.message.reply_text(
            "🤔 مفهمتش التعليق. جرب مثلاً:\n"
            "• خلي الإضاءة أغمق / افتح الإضاءة\n"
            "• قص أول 3 ثواني\n"
            "• غير الكابشن لـ ...\n"
            "• اسرع الفيديو / ابطأ"
        )
        return

    created_logs = []
    for op in parsed["operations"]:
        log = create_operation_log(
            user_id=user_id,
            video_id=video_id,
            operation_type=op["type"],
            parsed_value=op.get("value") or op.get("seconds") or op.get("new_text"),
            generated_prompt=op.get("prompt"),
            parent_version=get_video_version_info(video_id)["current_version"]
        )
        created_logs.append(log)

    ops_text = "\n".join(
        [f"• {l['operation_type']}: {l['parsed_value'] or ''} → {l['new_version']} (id: {l['operation_id']})"
         for l in created_logs]
    )
    await update.message.reply_text(
        f"📝 **Operation Plan Created**\n{ops_text}\n\n"
        "الحالة: PLAN_ONLY\n"
        "التعديل لم يُنفذ على فيديو فعلي لأن video-generation provider غير configured.",
        parse_mode="Markdown"
    )

# === Application setup with ENV ONLY token ===

def build_application():
    token = get_bot_token()  # Fail fast if absent
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_trending, pattern="show_trending"))
    app.add_handler(CallbackQueryHandler(handle_selection, pattern="select_"))
    app.add_handler(CallbackQueryHandler(handle_generate, pattern="generate_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_comment))
    return app

if __name__ == "__main__":
    # This will raise RuntimeError if BOT_TOKEN missing - clear startup fail
    application = build_application()
    # application.run_polling()  # Uncomment to run
    print("Bot application built successfully with ENV token - ready to run")
