#!/usr/bin/env python3
import hashlib
import hmac
import json
import mimetypes
import os
import sqlite3
import sys
import time
import uuid
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib import error as urlerror
from urllib import request as urlrequest


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "app.db"
DB_PATH = Path(os.environ.get("DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
DB_DIR = DB_PATH.parent
SESSION_COOKIE = "ipstudio_session"
PRODUCT_NAME = "IP智脑"
FREE_AI_LIMIT = int(os.environ.get("FREE_AI_LIMIT", "3"))
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

DEFAULT_PROFILE = {
    "account_name": "职场效率研究所",
    "niche": "职场效率 / AI 工具 / 普通人副业",
    "audience": "25-35 岁职场人，想提升效率和收入",
    "goal": "涨粉",
    "tone": "实用、直接、有案例、有步骤",
    "advantage": "懂 AI 工具，也能把方法拆成普通人能执行的步骤",
    "avoidance": "不做空泛鸡汤，不堆工具名，不做夸张收益承诺。",
}

DEFAULT_TOPICS = [
    {
        "title": "普通职场人如何用 AI 把周报从 1 小时压到 10 分钟",
        "category": "工具教程",
        "source": "方向推荐",
        "reason": "明确节省时间，痛点高频，适合做步骤型短视频。",
        "reference": "强调效率收益和可复制模板。",
        "score": 92,
    },
    {
        "title": "我用 3 个提示词做完竞品分析，老板以为我加班到半夜",
        "category": "经验故事",
        "source": "抖音参考",
        "reason": "故事钩子强，能强化懂工具、能落地的人设。",
        "reference": "参考职场反差型开头。",
        "score": 89,
    },
    {
        "title": "AI 工具很多，但真正能涨粉的内容结构只有这 4 种",
        "category": "痛点解决",
        "source": "手动添加",
        "reason": "面向博主焦虑，容易引导收藏和评论。",
        "reference": "适合做系列内容入口。",
        "score": 87,
    },
]

DIRECTION_TEMPLATES = [
    {
        "id": "direction-1",
        "category": "痛点解决",
        "title": "把低效工作拆成可复制流程",
        "angle": "围绕用户每天都在浪费时间的场景，给出 3-5 个可立即套用的步骤。",
        "formats": ["清单", "模板", "前后对比"],
    },
    {
        "id": "direction-2",
        "category": "经验故事",
        "title": "用个人经历建立可信人设",
        "angle": "把真实工作场景改写成故事，突出你如何用方法解决一个具体问题。",
        "formats": ["反差开头", "过程复盘", "结果展示"],
    },
    {
        "id": "direction-3",
        "category": "工具教程",
        "title": "把 AI 工具讲成普通人能用的方法",
        "angle": "少讲工具名，多讲场景、提示词、操作顺序和结果截图。",
        "formats": ["教程", "演示", "避坑"],
    },
    {
        "id": "direction-4",
        "category": "转化销售",
        "title": "用资料包或咨询承接高意向用户",
        "angle": "从免费方法过渡到模板、陪跑、咨询或社群，避免硬广感。",
        "formats": ["案例", "领取资料", "问题诊断"],
    },
]

HOT_REFERENCES = [
    {
        "id": "hot-1",
        "platform": "抖音",
        "title": "打工人用 AI 偷偷变强的 6 个工作流",
        "views": "218.6 万",
        "followers": "2.8 万",
        "category": "工具教程",
        "reason": "标题有身份代入和结果暗示，内容结构适合拆成系列。",
        "rewrite": "普通职场人用 AI 提升工作效率的 6 个工作流",
    },
    {
        "id": "hot-2",
        "platform": "抖音",
        "title": "别再瞎做账号了，先想清楚这 4 个定位问题",
        "views": "96.4 万",
        "followers": "1.1 万",
        "category": "痛点解决",
        "reason": "直接戳中账号迷茫，适合引导用户评论自己的赛道。",
        "rewrite": "普通人做个人 IP，先确认这 4 个定位问题",
    },
    {
        "id": "hot-3",
        "platform": "抖音",
        "title": "我靠一套选题表，把更新频率从每周 2 条提到每天 1 条",
        "views": "74.2 万",
        "followers": "8600",
        "category": "经验故事",
        "reason": "过程和结果都具体，能自然展示工具价值。",
        "rewrite": "内容生产慢的人，先搭一张能持续更新的选题表",
    },
    {
        "id": "hot-4",
        "platform": "抖音",
        "title": "账号没有记忆点？这 3 句话帮你定人设",
        "views": "63.8 万",
        "followers": "7200",
        "category": "人设定位",
        "reason": "适合做定位入口，能让用户保存并二次传播。",
        "rewrite": "个人 IP 没记忆点，用这 3 句话重新定义人设",
    },
]

DOUYIN_VIDEOS = [
    {
        "title": "普通人用 AI 写周报，10 分钟出一版",
        "views": 186000,
        "followers": 1280,
        "completion": 36,
        "engagement": 7.8,
        "revenue": 328,
        "suggestion": "保留“具体时间收益”的标题结构，下一条可扩展到会议纪要或复盘模板。",
    },
    {
        "title": "别再收藏工具清单，先搭自己的工作流",
        "views": 94200,
        "followers": 860,
        "completion": 41,
        "engagement": 9.4,
        "revenue": 216,
        "suggestion": "互动高，适合把评论里的工作场景整理成 3 条新选题。",
    },
    {
        "title": "3 个提示词做完竞品分析",
        "views": 238000,
        "followers": 2460,
        "completion": 29,
        "engagement": 6.1,
        "revenue": 512,
        "suggestion": "播放高但完播偏低，下一版要把结果展示提前到前 5 秒。",
    },
]


def connect():
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE,
              password_hash TEXT,
              is_guest INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
              token TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profiles (
              user_id INTEGER PRIMARY KEY,
              account_name TEXT NOT NULL,
              niche TEXT NOT NULL,
              audience TEXT NOT NULL,
              goal TEXT NOT NULL,
              tone TEXT NOT NULL,
              advantage TEXT NOT NULL,
              avoidance TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topics (
              id TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              category TEXT NOT NULL,
              source TEXT NOT NULL,
              reason TEXT NOT NULL,
              reference TEXT NOT NULL,
              score INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS style_samples (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              content TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
              user_id INTEGER PRIMARY KEY,
              plan TEXT NOT NULL,
              status TEXT NOT NULL,
              price REAL NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usage_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              action TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )


def now_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row):
    return dict(row) if row is not None else None


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return "%s$%s" % (salt, digest.hex())


def check_password(password, stored):
    if not stored or "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest)


def create_user(conn, email=None, password=None, is_guest=True):
    password_hash = hash_password(password) if password else None
    cur = conn.execute(
        """
        INSERT INTO users (email, password_hash, is_guest, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (email, password_hash, 1 if is_guest else 0, now_text()),
    )
    user_id = cur.lastrowid
    seed_user(conn, user_id)
    return user_id


def seed_user(conn, user_id):
    conn.execute(
        """
        INSERT OR IGNORE INTO profiles
        (user_id, account_name, niche, audience, goal, tone, advantage, avoidance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            DEFAULT_PROFILE["account_name"],
            DEFAULT_PROFILE["niche"],
            DEFAULT_PROFILE["audience"],
            DEFAULT_PROFILE["goal"],
            DEFAULT_PROFILE["tone"],
            DEFAULT_PROFILE["advantage"],
            DEFAULT_PROFILE["avoidance"],
        ),
    )
    for topic in DEFAULT_TOPICS:
        conn.execute(
            """
            INSERT OR IGNORE INTO topics
            (id, user_id, title, category, source, reason, reference, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "topic-" + uuid.uuid4().hex[:12],
                user_id,
                topic["title"],
                topic["category"],
                topic["source"],
                topic["reason"],
                topic["reference"],
                topic["score"],
                now_text(),
            ),
        )
    conn.execute(
        """
        INSERT OR IGNORE INTO subscriptions (user_id, plan, status, price, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, "creator-monthly", "inactive", 9.9, now_text()),
    )


def create_session(conn, user_id):
    token = uuid.uuid4().hex + uuid.uuid4().hex
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, now_text()),
    )
    return token


def get_topic(conn, user_id, topic_id):
    return conn.execute(
        "SELECT * FROM topics WHERE user_id = ? AND id = ?",
        (user_id, topic_id),
    ).fetchone()


def get_profile(conn, user_id):
    return conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()


def get_topics(conn, user_id):
    rows = conn.execute(
        "SELECT * FROM topics WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_subscription(conn, user_id):
    return row_to_dict(conn.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone())


def is_paid(subscription):
    return subscription and subscription.get("status") in ("active", "trialing")


def usage_count(conn, user_id):
    return conn.execute(
        "SELECT COUNT(*) AS total FROM usage_events WHERE user_id = ?",
        (user_id,),
    ).fetchone()["total"]


def usage_summary(conn, user_id):
    subscription = get_subscription(conn, user_id)
    used = usage_count(conn, user_id)
    return {
        "used": used,
        "limit": None if is_paid(subscription) else FREE_AI_LIMIT,
        "remaining": None if is_paid(subscription) else max(0, FREE_AI_LIMIT - used),
        "is_paid": bool(is_paid(subscription)),
    }


def quota_error(conn, user_id):
    usage = usage_summary(conn, user_id)
    if usage["is_paid"] or usage["remaining"] > 0:
        return None
    return {
        "error": "免费额度已用完，请开通 9.9 元/月订阅后继续使用 AI 功能。",
        "usage": usage,
    }


def record_usage(conn, user_id, action):
    conn.execute(
        "INSERT INTO usage_events (user_id, action, created_at) VALUES (?, ?, ?)",
        (user_id, action, now_text()),
    )
    return usage_summary(conn, user_id)


def deepseek_chat(system_prompt, user_prompt, temperature=0.7):
    if not DEEPSEEK_API_KEY:
        return None
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "stream": False,
    }
    req = urlrequest.Request(
        "%s/chat/completions" % DEEPSEEK_BASE_URL.rstrip("/"),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % DEEPSEEK_API_KEY,
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, json.JSONDecodeError, urlerror.URLError, TimeoutError) as exc:
        raise RuntimeError("DeepSeek 调用失败：%s" % exc)


def json_from_ai(text):
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def build_script(profile, topic, topics, style_sample_count):
    pool_context = "；".join([item["title"] for item in topics[:4]]) or topic["title"]
    style_context = (
        "已参考用户保存的风格样本，表达会更贴近用户历史文案。"
        if style_sample_count
        else "先按「%s」的风格生成，避免「%s」。" % (profile["tone"], profile["avoidance"])
    )
    return """标题：
{title}

3 秒开头：
如果你是{audience}，每天都被重复工作、选题和执行拖慢，先别急着找更多工具，先把一个流程跑顺。

正文口播：
今天用「{category}」这个角度，给你一个能直接照着做的方法。

第一步，先确认你的目标不是泛泛地变好，而是「{goal}」。目标不同，内容结构也不同。

第二步，把你的优势说具体。比如：{advantage}。观众不是因为工具关注你，而是因为你能把复杂问题变简单。

第三步，参考选题池里已经积累的方向：{pool_context}。这些内容共同指向一个账号记忆点：持续提供可执行的方法。

第四步，把这条内容落到一个可保存的结果上，例如清单、模板、避坑表或案例复盘。

结尾引导：
如果你也在做个人 IP，可以先把你的赛道和目标写下来。我会继续拆解普通人如何把选题池变成稳定更新系统。

封面文案：
别再随机发内容了，先搭一套能持续更新的选题池

风格参考：
{style_context}""".format(
        title=topic["title"],
        audience=profile["audience"],
        category=topic["category"],
        goal=profile["goal"],
        advantage=profile["advantage"],
        pool_context=pool_context,
        style_context=style_context,
    )


def build_ai_script(profile, topic, topics, style_sample_count, output_format):
    pool_context = "\n".join(["- %s（%s）" % (item["title"], item["category"]) for item in topics[:8]])
    system_prompt = (
        "你是%s的自媒体个人IP内容策划助手。"
        "你要帮助用户围绕账号定位、选题池和历史风格，生成可以直接编辑发布的中文内容。"
        "输出要具体、克制、可执行，不要夸张承诺，不要写成广告腔。"
    ) % PRODUCT_NAME
    user_prompt = """请生成一篇「{output_format}」。

账号名称：{account_name}
赛道：{niche}
目标群体：{audience}
当前目标：{goal}
内容风格：{tone}
可展示优势：{advantage}
避免：{avoidance}

本次选题：{title}
选题分类：{category}
入池原因：{reason}
参考来源：{reference}

选题池上下文：
{pool_context}

历史风格样本数量：{style_sample_count}

请按这个结构输出：
1. 标题
2. 3秒开头
3. 正文口播/正文内容
4. 结尾引导
5. 封面文案
6. 可拆成系列的后续选题 3 个
""".format(
        output_format=output_format,
        account_name=profile["account_name"],
        niche=profile["niche"],
        audience=profile["audience"],
        goal=profile["goal"],
        tone=profile["tone"],
        advantage=profile["advantage"],
        avoidance=profile["avoidance"],
        title=topic["title"],
        category=topic["category"],
        reason=topic["reason"],
        reference=topic["reference"],
        pool_context=pool_context,
        style_sample_count=style_sample_count,
    )
    return deepseek_chat(system_prompt, user_prompt, 0.75)


def analyze_content_with_ai(profile, content):
    system_prompt = (
        "你是%s的内容拆解助手。你只输出 JSON，不要输出 Markdown。"
        "JSON 字段必须是 insights 和 candidates。"
    ) % PRODUCT_NAME
    user_prompt = """请拆解用户历史文案，并返回 JSON：
{{
  "insights": [
    {{"label": "风格拆解", "title": "...", "copy": "..."}},
    {{"label": "结构建议", "title": "...", "copy": "..."}}
  ],
  "candidates": [
    {{"title": "...", "category": "历史文案回流", "reason": "..."}},
    {{"title": "...", "category": "痛点解决", "reason": "..."}},
    {{"title": "...", "category": "人设定位", "reason": "..."}}
  ]
}}

账号定位：
赛道：{niche}
受众：{audience}
目标：{goal}
风格：{tone}

用户历史文案：
{content}
""".format(
        niche=profile["niche"],
        audience=profile["audience"],
        goal=profile["goal"],
        tone=profile["tone"],
        content=content[:6000],
    )
    text = deepseek_chat(system_prompt, user_prompt, 0.45)
    return json_from_ai(text) if text else None


def analyze_douyin_with_ai(profile, account, raw_data):
    if not raw_data.strip():
        return None
    system_prompt = (
        "你是%s的数据复盘助手。你根据用户从抖音创作者服务中心复制/截图转写的数据，"
        "提炼增长结论。只输出 JSON，不要输出 Markdown。"
    ) % PRODUCT_NAME
    user_prompt = """请基于下面的抖音数据文本返回 JSON：
{{
  "status": "已读取 ...",
  "metrics": [{{"label": "总播放", "value": "..."}}, {{"label": "新增粉丝", "value": "..."}}],
  "videos": [
    {{"title": "...", "views": 0, "followers": 0, "completion": 0, "engagement": 0, "suggestion": "..."}}
  ],
  "diagnosis": [
    {{"title": "涨粉来源", "copy": "..."}},
    {{"title": "内容优化", "copy": "..."}},
    {{"title": "下一轮选题", "copy": "..."}}
  ]
}}

账号：{account}
赛道：{niche}
受众：{audience}
目标：{goal}

数据文本：
{raw_data}
""".format(
        account=account,
        niche=profile["niche"],
        audience=profile["audience"],
        goal=profile["goal"],
        raw_data=raw_data[:8000],
    )
    text = deepseek_chat(system_prompt, user_prompt, 0.35)
    return json_from_ai(text) if text else None


class AppHandler(BaseHTTPRequestHandler):
    server_version = "IPContentStudio/0.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (now_text(), fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api("GET", parsed)
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api("POST", parsed)
            return
        self.send_error(404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api("PUT", parsed)
            return
        self.send_error(404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api("DELETE", parsed)
            return
        self.send_error(404)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def cookie_token(self):
        header = self.headers.get("Cookie")
        if not header:
            return None
        jar = cookies.SimpleCookie()
        jar.load(header)
        item = jar.get(SESSION_COOKIE)
        return item.value if item else None

    def current_user(self, conn, create_guest=True):
        token = self.cookie_token()
        if token:
            row = conn.execute(
                """
                SELECT users.* FROM users
                JOIN sessions ON sessions.user_id = users.id
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()
            if row:
                return row_to_dict(row), None
        if not create_guest:
            return None, None
        user_id = create_user(conn, None, None, True)
        token = create_session(conn, user_id)
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_dict(user), token

    def send_json(self, payload, status=200, session_token=None, clear_session=False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if session_token:
            self.send_header(
                "Set-Cookie",
                "%s=%s; Path=/; HttpOnly; SameSite=Lax" % (SESSION_COOKIE, session_token),
            )
        if clear_session:
            self.send_header(
                "Set-Cookie",
                "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax" % SESSION_COOKIE,
            )
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, request_path):
        if request_path in ("", "/"):
            request_path = "/index.html"
        safe_path = os.path.normpath(request_path.lstrip("/"))
        file_path = (BASE_DIR / safe_path).resolve()
        if not str(file_path).startswith(str(BASE_DIR)) or not file_path.exists() or file_path.is_dir():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_api(self, method, parsed):
        try:
            with connect() as conn:
                if parsed.path == "/api/auth/register" and method == "POST":
                    self.api_register(conn)
                    return
                if parsed.path == "/api/auth/login" and method == "POST":
                    self.api_login(conn)
                    return
                if parsed.path == "/api/auth/logout" and method == "POST":
                    token = self.cookie_token()
                    if token:
                        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                    self.send_json({"ok": True}, clear_session=True)
                    return

                user, session_token = self.current_user(conn)
                if parsed.path == "/api/bootstrap" and method == "GET":
                    self.api_bootstrap(conn, user, session_token)
                    return
                if parsed.path == "/api/profile" and method == "PUT":
                    self.api_update_profile(conn, user)
                    return
                if parsed.path == "/api/topics" and method == "POST":
                    self.api_create_topic(conn, user)
                    return
                if parsed.path == "/api/topics" and method == "DELETE":
                    self.api_delete_topic(conn, user, parsed)
                    return
                if parsed.path == "/api/style-samples" and method == "POST":
                    self.api_style_sample(conn, user)
                    return
                if parsed.path == "/api/analyze-content" and method == "POST":
                    self.api_analyze_content(conn, user)
                    return
                if parsed.path == "/api/generate-script" and method == "POST":
                    self.api_generate_script(conn, user)
                    return
                if parsed.path == "/api/douyin/sync" and method == "POST":
                    self.api_douyin_sync(conn, user)
                    return
                if parsed.path == "/api/checkout" and method == "POST":
                    self.api_checkout(conn, user)
                    return
                self.send_json({"error": "Not found"}, 404)
        except sqlite3.IntegrityError as exc:
            self.send_json({"error": "数据已存在或不合法", "detail": str(exc)}, 400)
        except Exception as exc:
            self.send_json({"error": "服务器错误", "detail": str(exc)}, 500)

    def api_register(self, conn):
        data = self.read_json()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if "@" not in email or len(password) < 6:
            self.send_json({"error": "请输入邮箱和至少 6 位密码"}, 400)
            return
        user_id = create_user(conn, email, password, False)
        token = create_session(conn, user_id)
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        self.send_json({"ok": True, "user": self.public_user(user)}, session_token=token)

    def api_login(self, conn):
        data = self.read_json()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password(password, user["password_hash"]):
            self.send_json({"error": "邮箱或密码不正确"}, 401)
            return
        token = create_session(conn, user["id"])
        self.send_json({"ok": True, "user": self.public_user(user)}, session_token=token)

    def public_user(self, user):
        return {
            "id": user["id"],
            "email": user["email"],
            "is_guest": bool(user["is_guest"]),
        }

    def api_bootstrap(self, conn, user, session_token=None):
        profile = row_to_dict(get_profile(conn, user["id"]))
        topics = get_topics(conn, user["id"])
        style_count = conn.execute(
            "SELECT COUNT(*) AS total FROM style_samples WHERE user_id = ?",
            (user["id"],),
        ).fetchone()["total"]
        subscription = row_to_dict(
            conn.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user["id"],)).fetchone()
        )
        self.send_json(
            {
                "user": self.public_user(user),
                "profile": profile,
                "topics": topics,
                "style_sample_count": style_count,
                "subscription": subscription,
                "usage": usage_summary(conn, user["id"]),
                "directions": DIRECTION_TEMPLATES,
                "hot_references": HOT_REFERENCES,
                "ai_provider": "deepseek" if DEEPSEEK_API_KEY else "template",
            },
            session_token=session_token,
        )

    def api_update_profile(self, conn, user):
        data = self.read_json()
        profile = dict(DEFAULT_PROFILE)
        profile.update(
            {
                "account_name": data.get("account_name") or data.get("accountName") or DEFAULT_PROFILE["account_name"],
                "niche": data.get("niche") or DEFAULT_PROFILE["niche"],
                "audience": data.get("audience") or DEFAULT_PROFILE["audience"],
                "goal": data.get("goal") or DEFAULT_PROFILE["goal"],
                "tone": data.get("tone") or DEFAULT_PROFILE["tone"],
                "advantage": data.get("advantage") or DEFAULT_PROFILE["advantage"],
                "avoidance": data.get("avoidance") or DEFAULT_PROFILE["avoidance"],
            }
        )
        conn.execute(
            """
            UPDATE profiles
            SET account_name = ?, niche = ?, audience = ?, goal = ?, tone = ?, advantage = ?, avoidance = ?
            WHERE user_id = ?
            """,
            (
                profile["account_name"],
                profile["niche"],
                profile["audience"],
                profile["goal"],
                profile["tone"],
                profile["advantage"],
                profile["avoidance"],
                user["id"],
            ),
        )
        self.send_json({"ok": True, "profile": row_to_dict(get_profile(conn, user["id"]))})

    def api_create_topic(self, conn, user):
        data = self.read_json()
        title = (data.get("title") or "").strip()
        if not title:
            self.send_json({"error": "选题标题不能为空"}, 400)
            return
        existing = conn.execute(
            "SELECT * FROM topics WHERE user_id = ? AND title = ?",
            (user["id"], title),
        ).fetchone()
        if existing:
            self.send_json({"ok": True, "topic": row_to_dict(existing), "duplicate": True})
            return
        topic_id = "topic-" + uuid.uuid4().hex[:12]
        conn.execute(
            """
            INSERT INTO topics
            (id, user_id, title, category, source, reason, reference, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic_id,
                user["id"],
                title,
                data.get("category") or "痛点解决",
                data.get("source") or "手动添加",
                data.get("reason") or "用户加入选题池，后续文案会参考账号定位和选题池上下文。",
                data.get("reference") or "用户自定义选题",
                int(data.get("score") or 84 + (uuid.uuid4().int % 12)),
                now_text(),
            ),
        )
        topic = row_to_dict(get_topic(conn, user["id"], topic_id))
        self.send_json({"ok": True, "topic": topic})

    def api_delete_topic(self, conn, user, parsed):
        query = parse_qs(parsed.query)
        topic_id = (query.get("id") or [""])[0]
        conn.execute("DELETE FROM topics WHERE user_id = ? AND id = ?", (user["id"], topic_id))
        self.send_json({"ok": True})

    def api_style_sample(self, conn, user):
        data = self.read_json()
        content = (data.get("content") or "").strip()
        if content:
            conn.execute(
                "INSERT INTO style_samples (user_id, content, created_at) VALUES (?, ?, ?)",
                (user["id"], content[:4000], now_text()),
            )
        count = conn.execute(
            "SELECT COUNT(*) AS total FROM style_samples WHERE user_id = ?",
            (user["id"],),
        ).fetchone()["total"]
        self.send_json({"ok": True, "style_sample_count": count})

    def api_analyze_content(self, conn, user):
        blocked = quota_error(conn, user["id"])
        if blocked:
            self.send_json(blocked, 402)
            return
        data = self.read_json()
        content = (data.get("content") or "").strip()
        if not content:
            self.send_json({"error": "请先粘贴历史文案"}, 400)
            return
        conn.execute(
            "INSERT INTO style_samples (user_id, content, created_at) VALUES (?, ?, ?)",
            (user["id"], content[:4000], now_text()),
        )
        profile = get_profile(conn, user["id"])
        chunks = [item.strip() for item in content.split("\n\n") if item.strip()]
        first_line = next((line.strip() for line in content.splitlines() if line.strip()), "历史内容")
        fallback_candidates = [
            {
                "title": first_line.rstrip("。！？.!?") + "：适合继续做成系列内容",
                "category": "历史文案回流",
                "reason": "来自用户已写过的完整文案，说明这个方向已经符合用户表达习惯。",
            },
            {
                "title": "%s最常遇到的 3 个误区，可以从旧文案里继续拆" % profile["audience"],
                "category": "痛点解决",
                "reason": "旧文案中已有用户语气和案例，可以反推成更具体的痛点选题。",
            },
            {
                "title": "把已有内容整理成一套%s方法论" % profile["niche"],
                "category": "人设定位",
                "reason": "适合把零散文案升级成账号记忆点和系列栏目。",
            },
        ]
        fallback_insights = [
            {
                "label": "风格拆解",
                "title": profile["tone"],
                "copy": "已读取 %s 段内容。你的历史文案更适合沉淀为：场景痛点、具体步骤、案例复盘、结尾引导。"
                % max(1, len(chunks)),
            },
            {
                "label": "结构建议",
                "title": "系列化表达",
                "copy": "建议把旧文案拆成固定栏目，例如「一个问题」「三个步骤」「一个模板」「一个行动」。",
            },
        ]
        ai_payload = analyze_content_with_ai(row_to_dict(profile), content)
        insights = (ai_payload or {}).get("insights") or fallback_insights
        candidates = (ai_payload or {}).get("candidates") or fallback_candidates
        count = conn.execute(
            "SELECT COUNT(*) AS total FROM style_samples WHERE user_id = ?",
            (user["id"],),
        ).fetchone()["total"]
        usage = record_usage(conn, user["id"], "analyze_content")
        self.send_json(
            {
                "ok": True,
                "style_sample_count": count,
                "insights": insights,
                "candidates": candidates,
                "usage": usage,
            }
        )

    def api_generate_script(self, conn, user):
        blocked = quota_error(conn, user["id"])
        if blocked:
            self.send_json(blocked, 402)
            return
        data = self.read_json()
        topic_id = data.get("topic_id") or data.get("topicId")
        topic = get_topic(conn, user["id"], topic_id)
        if not topic:
            topics = get_topics(conn, user["id"])
            if not topics:
                self.send_json({"error": "选题池为空"}, 400)
                return
            topic = topics[0]
        else:
            topic = row_to_dict(topic)
        profile = row_to_dict(get_profile(conn, user["id"]))
        topics = get_topics(conn, user["id"])
        style_count = conn.execute(
            "SELECT COUNT(*) AS total FROM style_samples WHERE user_id = ?",
            (user["id"],),
        ).fetchone()["total"]
        output_format = data.get("format") or "短视频口播稿"
        script = build_ai_script(profile, topic, topics, style_count, output_format) or build_script(
            profile, topic, topics, style_count
        )
        usage = record_usage(conn, user["id"], "generate_script")
        self.send_json(
            {
                "ok": True,
                "script": script,
                "topic": topic,
                "usage": usage,
            }
        )

    def api_douyin_sync(self, conn, user):
        blocked = quota_error(conn, user["id"])
        if blocked:
            self.send_json(blocked, 402)
            return
        data = self.read_json()
        account = data.get("account") or "@职场效率研究所"
        raw_data = data.get("raw_data") or data.get("rawData") or ""
        profile = row_to_dict(get_profile(conn, user["id"]))
        ai_review = analyze_douyin_with_ai(profile, account, raw_data)
        if ai_review:
            ai_review["ok"] = True
            ai_review["account"] = account
            ai_review["usage"] = record_usage(conn, user["id"], "douyin_review")
            self.send_json(ai_review)
            return
        total_views = sum(item["views"] for item in DOUYIN_VIDEOS)
        total_followers = sum(item["followers"] for item in DOUYIN_VIDEOS)
        total_revenue = sum(item["revenue"] for item in DOUYIN_VIDEOS)
        avg_completion = round(sum(item["completion"] for item in DOUYIN_VIDEOS) / len(DOUYIN_VIDEOS))
        best = sorted(DOUYIN_VIDEOS, key=lambda item: item["followers"], reverse=True)[0]
        usage = record_usage(conn, user["id"], "douyin_review")
        self.send_json(
            {
                "ok": True,
                "account": account,
                "status": "已读取 %s 的演示数据。上线版建议让用户粘贴创作者服务中心数据后由 AI 复盘。" % account,
                "metrics": [
                    {"label": "总播放", "value": "%.1f 万" % (total_views / 10000)},
                    {"label": "新增粉丝", "value": "{:,}".format(total_followers)},
                    {"label": "平均完播", "value": "%s%%" % avg_completion},
                    {"label": "内容收入", "value": "¥{:,}".format(total_revenue)},
                ],
                "videos": DOUYIN_VIDEOS,
                "diagnosis": [
                    {
                        "title": "涨粉来源",
                        "copy": "最近最能带粉的是「%s」，建议把它拆成 3 条同结构选题继续测试。" % best["title"],
                    },
                    {
                        "title": "内容优化",
                        "copy": "完播低于 35% 的内容需要把结果展示提前；互动高的内容可以直接回流到选题池。",
                    },
                    {
                        "title": "自动建议",
                        "copy": "下一轮优先做「AI 工作流」「选题系统」「个人 IP 定位」三个方向，并保留具体收益型标题。",
                    },
                ],
                "usage": usage,
            }
        )

    def api_checkout(self, conn, user):
        conn.execute(
            """
            UPDATE subscriptions
            SET plan = ?, status = ?, price = ?, updated_at = ?
            WHERE user_id = ?
            """,
            ("creator-monthly", "pending_payment_provider", 9.9, now_text(), user["id"]),
        )
        self.send_json(
            {
                "ok": True,
                "message": "支付通道待接入。这里会跳转到微信支付或支付宝。",
                "subscription": row_to_dict(
                    conn.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user["id"],)).fetchone()
                ),
            }
        )


def main():
    init_db()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print("%s running at http://%s:%s" % (PRODUCT_NAME, host, port))
    server.serve_forever()


if __name__ == "__main__":
    main()
