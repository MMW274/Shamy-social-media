"""Long-running Telegram listener that updates the post log on button taps."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from pipeline.config import load_settings

LOG_PATH = Path("data/content-log.jsonl")
APPROVALS_PATH = Path("data/approvals.jsonl")

log = logging.getLogger("shamy.listener")


def _record_decision(slot_id: str, decision: str, variant: int | None = None) -> None:
    APPROVALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "slot_id": slot_id,
        "decision": decision,
        "variant": variant,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    with APPROVALS_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q or not q.data:
        return
    await q.answer()
    parts = q.data.split("|")
    action = parts[0]
    slot_id = parts[1] if len(parts) > 1 else "?"
    variant = int(parts[2]) if len(parts) > 2 else None

    if action == "approve":
        _record_decision(slot_id, "approved", variant)
        await q.edit_message_caption(
            caption=f"✅ Approved (V{variant}) — {slot_id}\n\nNow publish via Vizard."
        )
    elif action == "skip":
        _record_decision(slot_id, "skipped")
        await q.edit_message_caption(caption=f"⏭️ Skipped — {slot_id}")
    elif action == "block":
        _record_decision(slot_id, "blocked")
        await q.edit_message_caption(
            caption=f"🚫 Blocked — {slot_id}\n\nPlease move this asset to 02_humans_in_frame/ in Drive."
        )
    elif action == "edit":
        _record_decision(slot_id, "edit_requested")
        await q.edit_message_caption(
            caption=f"✏️ Edit requested for {slot_id}.\nReply to this message with the new caption."
        )


async def main_async() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = load_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CallbackQueryHandler(on_button))
    log.info("Listener up. Waiting for button taps…")
    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    asyncio.run(main_async())
