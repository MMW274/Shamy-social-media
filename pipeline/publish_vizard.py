"""Vizard.ai Open API — submit short video, poll, publish to connected social accounts."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests

BASE = "https://elb-api.vizard.ai/hvizard-server-front/open-api/v1/project"
POLL_SECONDS = 30
MAX_WAIT_SECONDS = 20 * 60


@dataclass(frozen=True)
class SocialAccount:
    id: str
    platform: str
    username: str
    status: str


@dataclass(frozen=True)
class OutputVideo:
    video_id: int
    video_url: str
    title: str


def api_key_from_env() -> str:
    key = os.getenv("VIZARD_API_KEY") or os.getenv("PRODUCTION")
    if not key:
        raise RuntimeError("Set VIZARD_API_KEY or PRODUCTION in the environment")
    return key


def _headers(api_key: str) -> dict[str, str]:
    return {"VIZARDAI_API_KEY": api_key, "Content-Type": "application/json"}


def list_social_accounts(api_key: str) -> list[SocialAccount]:
    resp = requests.get(f"{BASE}/social-accounts", headers=_headers(api_key), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    accounts = []
    for item in data.get("publishAccounts", []):
        accounts.append(
            SocialAccount(
                id=str(item["id"]),
                platform=item.get("platform", ""),
                username=item.get("username", ""),
                status=item.get("status", ""),
            )
        )
    return accounts


def find_x_account(accounts: list[SocialAccount]) -> SocialAccount:
    for acct in accounts:
        if acct.platform.lower() in {"twitter", "twitter(x)", "x"} and acct.status == "active":
            return acct
    names = [f"{a.platform}:{a.username} ({a.status})" for a in accounts]
    raise RuntimeError(f"No active X/Twitter account found. Connected: {names}")


def submit_short_video(
    api_key: str,
    video_url: str,
    *,
    ext: str = "mp4",
    project_name: str = "Shamy post",
    ratio: int = 4,
) -> int:
    """Submit a short video (<3 min) for light editing. Returns projectId."""
    payload: dict[str, Any] = {
        "getClips": 0,
        "videoUrl": video_url,
        "videoType": 1,
        "ext": ext,
        "lang": "en",
        "ratioOfClip": ratio,
        "subtitleSwitch": 0,
        "headlineSwitch": 0,
        "emojiSwitch": 0,
        "projectName": project_name,
    }
    resp = requests.post(f"{BASE}/create", headers=_headers(api_key), json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") not in (2000, None) and "projectId" not in data:
        raise RuntimeError(f"Vizard create failed: {data}")
    project_id = data.get("projectId") or data.get("data", {}).get("projectId")
    if not project_id:
        raise RuntimeError(f"No projectId in response: {data}")
    return int(project_id)


def wait_for_videos(api_key: str, project_id: int) -> list[OutputVideo]:
    deadline = time.time() + MAX_WAIT_SECONDS
    while time.time() < deadline:
        resp = requests.get(f"{BASE}/query/{project_id}", headers=_headers(api_key), timeout=120)
        resp.raise_for_status()
        data = resp.json()
        videos_raw = data.get("videos") or data.get("data", {}).get("videos") or []
        if videos_raw:
            return [
                OutputVideo(
                    video_id=int(v["videoId"]),
                    video_url=v.get("videoUrl", ""),
                    title=v.get("title", ""),
                )
                for v in videos_raw
            ]
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"Vizard project {project_id} not ready after {MAX_WAIT_SECONDS}s")


def publish_video(
    api_key: str,
    *,
    final_video_id: int,
    social_account_id: str,
    post: str,
    publish_time_ms: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "finalVideoId": final_video_id,
        "socialAccountId": social_account_id,
        "post": post,
    }
    if publish_time_ms is not None:
        payload["publishTime"] = publish_time_ms
    resp = requests.post(
        f"{BASE}/publish-video", headers=_headers(api_key), json=payload, timeout=120
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 2000:
        raise RuntimeError(f"Publish failed: {data}")
    return data


def generate_x_caption(api_key: str, final_video_id: int, fallback: str) -> str:
    payload = {
        "finalVideoId": final_video_id,
        "aiSocialPlatform": 7,
        "tone": 1,
        "voice": 0,
    }
    resp = requests.post(f"{BASE}/ai-social", headers=_headers(api_key), json=payload, timeout=120)
    if resp.status_code != 200:
        return fallback
    data = resp.json()
    caption = data.get("caption") or data.get("post") or data.get("data", {}).get("caption")
    return caption if caption else fallback
