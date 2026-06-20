"""CN: 体验层内容仓库，保存首页和后台编排所需的内容块。
EN: Experience-content repository for homepage and admin orchestration blocks.
"""

from __future__ import annotations

import copy
import json

from app.core.storage import connect


CONTENT_KEY = "homepage"


def get_experience_content(database_url: str) -> dict:
    with connect(database_url) as connection:
        row = connection.execute(
            "SELECT payload_json FROM experience_contents WHERE content_key = ?",
            (CONTENT_KEY,),
        ).fetchone()
    if row is None:
        return copy.deepcopy(_default_content())
    return json.loads(row["payload_json"])


def save_experience_content(database_url: str, payload: dict) -> dict:
    normalized = dict(payload)
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO experience_contents (content_key, payload_json)
            VALUES (?, ?)
            ON CONFLICT(content_key) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                CONTENT_KEY,
                json.dumps(normalized, ensure_ascii=False),
            ),
        )
    return normalized


def _default_content() -> dict:
    return {
        "hero": {
            "eyebrow": "LIFESTYLE JOURNAL · 背包里的骑行日记",
            "title": "今天不训练，只是在城市里收集一点阳光。",
            "lead": "Over Cycling 帮偶尔骑车的人找到轻松路线、咖啡停靠点和适合今天的出门理由。它更像一本随身带着的旅行手账，温柔地邀请你离开屏幕。",
            "primary_cta": "让 AI 伙伴帮我安排",
            "secondary_cta": "看看周末建议",
        },
        "today_nudges": [
            {"title": "天气便签", "body": "傍晚温度刚好，适合找树多、风轻的路线。"},
            {"title": "今日慢骑便条", "body": "把目标降一点，留出停下来喝水和看风景的时间。"},
            {"title": "心情边注", "body": "如果今天脑子很满，就选一条不需要证明自己的路。"},
        ],
        "curated_routes": [
            {
                "route_code": "HZ-LEISURE-003",
                "section_label": "公园剪贴页",
                "title": "梧桐树荫小环线",
                "summary": "适合傍晚散掉一点白天留下的噪音。",
                "tags": ["公园", "树荫", "轻松"],
            },
            {
                "route_code": "HZ-RIVER-001",
                "section_label": "咖啡停靠页",
                "title": "河边拿铁停靠点",
                "summary": "顺着江边慢慢骑，路上留一个不赶时间的窗口。",
                "tags": ["江边", "咖啡", "周末上午"],
            },
            {
                "route_code": "HZ-HILL-002",
                "section_label": "日落光影页",
                "title": "橘色桥面慢行",
                "summary": "风景更重要，配速和成绩都可以晚点再说。",
                "tags": ["日落", "拍照", "风景"],
            },
        ],
        "companion_persona": {
            "headline": "不是教练，是替你翻开周末的人。",
            "description": "它像一位熟悉城市小路的同行者，记得你喜欢树荫、咖啡和不太拥挤的路，也会在你累的时候把计划变短。",
            "quick_prompts": [
                "帮我生成一个不累的周末骑行计划",
                "找一个可以顺路买咖啡的路线",
                "推荐附近安静一点的公园",
                "帮我记录今天的小骑行记忆",
            ],
        },
        "weekend_plan_templates": [
            {"slug": "quiet", "title": "安静公园", "summary": "适合放空和轻松呼吸的周末半日骑。"},
            {"slug": "coffee", "title": "咖啡窗口", "summary": "把路线和停靠点拼成一张不着急的小计划。"},
            {"slug": "sunset", "title": "日落拍照", "summary": "留一点金色的时间给桥面、河岸和风。"},
        ],
        "journal_cards": [
            {"label": "今天看到", "title": "桥下有人吹萨克斯。"},
            {"label": "适合下次", "title": "再早 20 分钟出门。"},
            {"label": "停靠点", "title": "河边咖啡窗口。"},
            {"label": "心情", "title": "屏幕外的风很轻。"},
        ],
        "cta_footer": {
            "quote": "如果今天只是想换一口空气，那也已经足够了。",
            "lead": "打开 Over Cycling，让 AI 伙伴帮你找一条不需要证明自己的路。",
            "button_label": "从一句心情开始",
        },
    }
