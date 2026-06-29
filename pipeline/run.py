"""CLI entrypoint: propose a single slot end-to-end."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.brand import load_brand_voice
from pipeline.caption import configure as configure_caption, generate as generate_caption, validate_caption
from pipeline.config import load_settings
from pipeline.drive import authorize as drive_auth, download_file, list_folder_recursive
from pipeline.postlog import PostRecord, append_record, is_duplicate, load_all
from pipeline.privacy import configure as configure_privacy, check_image, is_safe_to_post
from pipeline.selector import DriveFile as SelectorFile, select_asset
from pipeline.slots import Platform, slot_from_dict
from pipeline.telegram_bot import ApprovalCard, send_approval_sync


CALENDAR_PATH = Path("data/content-calendar.json")
LOG_PATH = Path("data/content-log.jsonl")
TMP_DIR = Path("local/tmp")


def _cat_from_folder(folder: str) -> str:
    if folder.endswith("_amy"):
        return "Amy"
    if folder.endswith("_sheldon"):
        return "Sheldon"
    if folder.endswith("_both"):
        return "Amy and Sheldon"
    return "Amy and Sheldon"


def cmd_propose(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    log = logging.getLogger("shamy.run")

    settings = load_settings()
    bv = load_brand_voice("data/brand-voice.yaml")

    calendar = json.loads(CALENDAR_PATH.read_text())
    target_date = date.fromisoformat(args.date)
    slot_dicts = [
        s for s in calendar["slots"]
        if date.fromisoformat(s["date"]) == target_date and s["platform"] == args.platform
    ]
    if not slot_dicts:
        log.error("No slot in calendar for %s / %s", args.date, args.platform)
        return 2
    slot = slot_from_dict(slot_dicts[0])
    log.info("Slot: %s pillar=%s", slot.id, slot.pillar)

    if is_duplicate(LOG_PATH, slot.id):
        log.warning("Slot %s already posted — skipping.", slot.id)
        return 0

    log.info("Authorising Drive…")
    svc = drive_auth()
    drive_files = list_folder_recursive(svc, settings.drive_root_folder_id)
    log.info("Drive: %d files across safe folders", len(drive_files))

    used = {r.asset_path for r in load_all(LOG_PATH)}
    selector_files = [
        SelectorFile(id=f.id, name=f.name, folder=f.folder, mime_type=f.mime_type)
        for f in drive_files
    ]
    pick = select_asset(selector_files, pillar=slot.pillar, used_ids=used)
    if not pick:
        log.error("No asset matches pillar=%s. Send Sneha a nudge.", slot.pillar)
        return 3

    log.info("Picked: %s/%s", pick.folder, pick.name)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    local_path = download_file(svc, pick.id, TMP_DIR / pick.name)

    configure_privacy(settings.gemini_api_key)
    verdict = check_image(local_path)
    log.info("Privacy: %s (conf=%.2f)", "BLOCK" if verdict.has_human else "OK", verdict.confidence)
    if not is_safe_to_post(verdict):
        log.error("Privacy check blocked: %s", verdict.reason)
        return 4

    configure_caption(settings.gemini_api_key)
    cat = _cat_from_folder(pick.folder)
    cap = generate_caption(local_path, bv, slot.pillar, cat)
    issues = validate_caption(cap, bv)
    if issues:
        log.warning("Caption issues: %s", "; ".join(issues))

    card = ApprovalCard(
        slot_id=slot.id,
        platform=slot.platform.value,
        pillar=slot.pillar,
        image_path=local_path,
        variants=cap.variants,
        hashtags=cap.hashtags,
        sound_url=None,
    )

    if settings.dry_run:
        log.info("DRY RUN — skipping Telegram send")
        log.info(
            "Card payload: slot=%s pillar=%s variants=%s hashtags=%s",
            card.slot_id, card.pillar, card.variants, card.hashtags,
        )
    else:
        for chat_id in (settings.telegram_chat_id_sneha, settings.telegram_chat_id_mehul):
            send_approval_sync(settings.telegram_bot_token, chat_id, card)
        log.info("Approval card sent.")

    record = PostRecord(
        slot_id=slot.id,
        platform=slot.platform.value,
        pillar=slot.pillar,
        asset_path=f"{pick.folder}/{pick.name}",
        caption="(proposed)",
        hashtags=cap.hashtags,
        timestamp_utc=datetime.now(timezone.utc),
        sound_url=None,
        external_post_id=None,
    )
    append_record(LOG_PATH, record)
    log.info("Recorded proposal in %s", LOG_PATH)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("shamy")
    sub = p.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("propose", help="Propose a single slot")
    pr.add_argument("--date", required=True, help="YYYY-MM-DD")
    pr.add_argument("--platform", required=True, choices=[x.value for x in Platform])
    pr.set_defaults(func=cmd_propose)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
