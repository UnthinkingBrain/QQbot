#!/usr/bin/env python3
import os
import json
import time
import asyncio
import websockets
import yaml
from openai import OpenAI
from collections import defaultdict

# =========================
# ENV
# =========================

WS_URL = os.getenv("WS_URL")
API_KEY = os.getenv("NVIDIA_API_KEY")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)

# =========================
# YAML 工单存储
# =========================

TICKET_FILE = "tickets.yaml"

def load_tickets():
    if not os.path.exists(TICKET_FILE):
        return {}
    with open(TICKET_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data else {}

def save_tickets(data):
    with open(TICKET_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True)

def create_ticket(category, priority, content):
    tickets = load_tickets()

    ticket_id = str(int(time.time() * 1000))

    tickets[ticket_id] = {
        "category": category,
        "priority": priority,
        "content": content,
        "status": "new",
        "time": time.time()
    }

    save_tickets(tickets)
    return ticket_id

# =========================
# 用户记忆（私聊）
# =========================

user_memory = defaultdict(list)

# =========================
# 去重缓存
# =========================

merge_buffer = defaultdict(list)
MERGE_WINDOW = 120

def merge_check(category, text):
    now = time.time()
    merge_buffer[category].append((now, text))

    merge_buffer[category] = [
        x for x in merge_buffer[category]
        if now - x[0] < MERGE_WINDOW
    ]

    return len(merge_buffer[category]) > 1

# =========================
# QQ 分流表
# =========================

QQ_MAP = {
    "washer": [{"type": "at", "data": {"qq": "<QQ_ID_1>"}}],
    "bathroom": [{"type": "at", "data": {"qq": "<QQ_ID_2>"}}],
    "property": [{"type": "at", "data": {"qq": "<QQ_ID_3>"}}],
    "water": [{"type": "at", "data": {"qq": "<QQ_ID_4>"}}],
    "hydropower": [{
        "type": "text",
        "data": {"text": "后勤或水电中心联系电话"}
    }]
}

# =========================
# Prompt
# =========================

CLASSIFY_PROMPT = """
返回JSON：
{
  "category": "washer|bathroom|property|water|hydropower|other",
  "priority": "urgent|normal|low"
}
只输出JSON
"""

CHAT_PROMPT = "宿舍AI助手"

# =========================
# LLM
# =========================

def call_llm(messages):
    try:
        resp = client.chat.completions.create(
            model="deepseek-ai/deepseek-v4-pro",
            messages=messages
        )
        return resp.choices[0].message.content
    except:
        return None

def classify(text):
    raw = call_llm([
        {"role": "system", "content": CLASSIFY_PROMPT},
        {"role": "user", "content": text}
    ])

    try:
        return json.loads(raw)
    except:
        return {"category": "other", "priority": "low"}

def chat(user_id, msg):
    user_memory[user_id].append({"role": "user", "content": msg})

    resp = call_llm([
        {"role": "system", "content": CHAT_PROMPT},
        *user_memory[user_id]
    ])

    user_memory[user_id].append({"role": "assistant", "content": resp})
    return resp

# =========================
# 群消息处理
# =========================

async def handle_group(ws, data):

    raw = data["raw_message"]
    group_id = data["group_id"]
    message_id = data["message_id"]

    result = classify(raw)

    category = result["category"]
    priority = result["priority"]

    if category == "other":
        return

    if merge_check(category, raw):
        return

    ticket_id = create_ticket(category, priority, raw)

    message = [
        {"type": "reply", "data": {"id": str(message_id)}},
        {
            "type": "text",
            "data": {
                "text": f"[工单:{ticket_id}] {category} | {priority}"
            }
        }
    ]

    if category in QQ_MAP:
        message += QQ_MAP[category]

    await ws.send(json.dumps({
        "action": "send_group_msg",
        "params": {
            "group_id": group_id,
            "message": message
        }
    }, ensure_ascii=False))

# =========================
# 私聊处理
# =========================

async def handle_private(ws, data):

    uid = data["user_id"]
    msg = data["raw_message"]
    mid = data["message_id"]

    reply = chat(uid, msg)

    await ws.send(json.dumps({
        "action": "send_private_msg",
        "params": {
            "user_id": uid,
            "message": [
                {"type": "reply", "data": {"id": str(mid)}},
                {"type": "text", "data": {"text": reply}}
            ]
        }
    }, ensure_ascii=False))

# =========================
# 路由
# =========================

async def handle(ws, data):

    if data.get("message_type") == "group":
        await handle_group(ws, data)

    elif data.get("message_type") == "private":
        await handle_private(ws, data)

# =========================
# 主循环
# =========================

async def main():

    if not WS_URL or not API_KEY:
        raise ValueError("ENV not set")

    async with websockets.connect(WS_URL) as ws:

        while True:
            try:
                raw = await ws.recv()
                data = json.loads(raw)

                if data.get("post_type") != "message":
                    continue

                asyncio.create_task(handle(ws, data))

            except:
                continue


if __name__ == "__main__":
    asyncio.run(main())