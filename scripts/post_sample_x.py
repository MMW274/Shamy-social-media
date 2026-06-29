#!/usr/bin/env python3
"""One-shot: publish the Shamy neighborhood-watch sample clip to @LifeWithShamy on X via Vizard."""
from __future__ import annotations

import argparse
import os
import sys

from pipeline.publish_vizard import (
    api_key_from_env,
    find_x_account,
    list_social_accounts,
    publish_video,
    submit_short_video,
    wait_for_videos,
)

# X limit 280 chars — brand voice, no human names
DEFAULT_CAPTION = (
    "Neighborhood watch is in session. Amy handles reconnaissance. "
    "Sheldon handles quality control. Neither has approved the birds. 🐾\n\n"
    "#LifeWithShamy #AmyAndSheldon #CatsOfTwitter #RescueCats"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Shamy sample post to X via Vizard")
    parser.add_argument(
        "--video-url",
        required=True,
        help="Public direct URL to an MP4 (e.g. raw.githubusercontent.com/.../samples/neighborhood-watch.mp4)",
    )
    parser.add_argument("--caption", default=DEFAULT_CAPTION, help="X post text (max 280 chars)")
    parser.add_argument("--dry-run", action="store_true", help="List accounts only, do not publish")
    args = parser.parse_args()

    if len(args.caption) > 280:
        print(f"Warning: caption is {len(args.caption)} chars; X limit is 280. Truncating.")
        args.caption = args.caption[:277] + "..."

    api_key = api_key_from_env()
    print("Fetching connected social accounts…")
    accounts = list_social_accounts(api_key)
    for a in accounts:
        print(f"  - {a.platform} @{a.username} [{a.status}] id={a.id}")

    x_acct = find_x_account(accounts)
    print(f"\nTarget X account: @{x_acct.username} (id={x_acct.id})")

    if args.dry_run:
        print("\nDry run — stopping before submit/publish.")
        return 0

    print(f"\nSubmitting video to Vizard: {args.video_url}")
    project_id = submit_short_video(api_key, args.video_url, project_name="Shamy sample — neighborhood watch")
    print(f"Project id: {project_id} — waiting for render (up to ~20 min)…")

    videos = wait_for_videos(api_key, project_id)
    video = videos[0]
    print(f"Ready: videoId={video.video_id} title={video.title!r}")

    print(f"\nPublishing to X with caption:\n{args.caption}\n")
    result = publish_video(
        api_key,
        final_video_id=video.video_id,
        social_account_id=x_acct.id,
        post=args.caption,
    )
    print(f"Success: {result}")
    print("Check https://x.com/LifeWithShamy — post may take a minute to appear.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
