"""Telegram approval card — sends photo + caption variants, listens for button taps."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CallbackQueryHandler


@dataclass(frozen=True)
class ApprovalCard:
    slot_id: str
    platform: str
    pillar: str
    image_path: Path
    variants: list[str]
    hashtags: list[str]
    sound_url: str | None = None


def _format_caption(card: ApprovalCard) -> str:
    lines = [
        f"🐾 *{card.slot_id}* — `{card.platform}` · _{card.pillar}_",
        "",
        "*Variant 1 (short, cat-POV):*",
        card.variants[0] if card.variants else "(missing)",
        "",
        "*Variant 2 (medium, joke):*",
        card.variants[1] if len(card.variants) > 1 else "(missing)",
        "",
        "*Variant 3 (narrator):*",
        card.variants[2] if len(card.variants) > 2 else "(missing)",
        "",
        "*Hashtags:* " + " ".join(card.hashtags),
    ]
    if card.sound_url:
        lines += ["", f"🎵 [Suggested sound]({card.sound_url})"]
    return "\n".join(lines)


def _keyboard(slot_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve V1", callback_data=f"approve|{slot_id}|1"),
            InlineKeyboardButton("✅ V2",         callback_data=f"approve|{slot_id}|2"),
            InlineKeyboardButton("✅ V3",         callback_data=f"approve|{slot_id}|3"),
        ],
        [
            InlineKeyboardButton("✏️ Edit",  callback_data=f"edit|{slot_id}"),
            InlineKeyboardButton("⏭️ Skip",  callback_data=f"skip|{slot_id}"),
            InlineKeyboardButton("🚫 Block", callback_data=f"block|{slot_id}"),
        ],
    ])


async def send_approval(bot_token: str, chat_id: int, card: ApprovalCard) -> int:
    """Send an approval card. Returns the message_id for later editing."""
    app = Application.builder().token(bot_token).build()
    async with app:
        with card.image_path.open("rb") as fh:
            msg = await app.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(fh),
                caption=_format_caption(card),
                parse_mode="Markdown",
                reply_markup=_keyboard(card.slot_id),
            )
        return msg.message_id


def send_approval_sync(bot_token: str, chat_id: int, card: ApprovalCard) -> int:
    return asyncio.run(send_approval(bot_token, chat_id, card))
