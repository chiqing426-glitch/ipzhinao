const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const MODEL = "deepseek-chat";

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json; charset=utf-8" },
  });
}

function systemPrompt() {
  return [
    "你是 IP智脑 的内容增长顾问，服务自媒体博主和个人 IP。",
    "回答必须是严格 JSON，不要 Markdown，不要代码块。",
    "内容要具体、可执行、适合中国自媒体语境，尤其是抖音、小红书、公众号。",
    "不要虚构真实平台数据，可以做爆款结构建议，但不要声称已经实时搜索全网。",
  ].join("\n");
}

function extractJson(text) {
  const cleaned = text.trim().replace(/^```json\s*/i, "").replace(/^```\s*/i, "").replace(/```$/i, "").trim();
  try {
    return JSON.parse(cleaned);
  } catch (_error) {
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start >= 0 && end > start) return JSON.parse(cleaned.slice(start, end + 1));
    throw new Error("AI response is not valid JSON");
  }
}

async function deepseek(env, userPrompt) {
  if (!env.DEEPSEEK_API_KEY) throw new Error("Missing DEEPSEEK_API_KEY");
  const response = await fetch("https://api.deepseek.com/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${env.DEEPSEEK_API_KEY}`,
    },
    body: JSON.stringify({
      model: env.DEEPSEEK_MODEL || MODEL,
      temperature: 0.7,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: systemPrompt() },
        { role: "user", content: userPrompt },
      ],
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`DeepSeek error ${response.status}: ${detail}`);
  }
  const data = await response.json();
  return extractJson(data.choices?.[0]?.message?.content || "{}");
}

function compact(value) {
  return JSON.stringify(value, null, 2);
}

async function profileFeedback(request, env) {
  const { profile, topics } = await request.json();
  const prompt = `
请基于以下个人 IP 档案，输出定位反馈、选题方向和爆款参考。

档案：
${compact(profile)}

当前选题池：
${compact(topics || [])}

请返回 JSON：
{
  "feedback": {
    "summary": "一段 60-100 字定位判断",
    "items": [
      {"label":"定位判断","title":"...","copy":"..."},
      {"label":"受众洞察","title":"...","copy":"..."},
      {"label":"内容策略","title":"...","copy":"..."},
      {"label":"风险提醒","title":"...","copy":"..."}
    ]
  },
  "directions": [
    {"id":"ai-direction-1","category":"痛点解决","title":"...","angle":"...","formats":["清单","教程","案例"]},
    {"id":"ai-direction-2","category":"经验故事","title":"...","angle":"...","formats":["反差开头","过程复盘","结果展示"]},
    {"id":"ai-direction-3","category":"工具教程","title":"...","angle":"...","formats":["演示","模板","避坑"]},
    {"id":"ai-direction-4","category":"转化销售","title":"...","angle":"...","formats":["案例","领取资料","评论互动"]}
  ],
  "hot_references": [
    {"id":"ai-hot-1","platform":"抖音","title":"...","views":"结构参考","followers":"涨粉强","category":"...","reason":"...","rewrite":"..."}
  ]
}
`;
  return json({ ok: true, ...(await deepseek(env, prompt)) });
}

async function generateScript(request, env) {
  const { profile, topic, topics, format } = await request.json();
  const prompt = `
请为自媒体账号生成一篇可直接修改的完整文案。

账号档案：
${compact(profile)}

当前选题：
${compact(topic)}

选题池上下文：
${compact(topics || [])}

输出形式：${format || "短视频口播稿"}

请返回 JSON：
{
  "script": "包含标题、开头3秒、正文结构、完整口播/正文、互动结尾。要具体，不要泛泛而谈。"
}
`;
  return json({ ok: true, ...(await deepseek(env, prompt)) });
}

async function analyzeContent(request, env) {
  const { profile, content, topics } = await request.json();
  const prompt = `
请拆解用户过去的完整文案，分析表达风格，并反推出可回流到选题池的新选题。

账号档案：
${compact(profile)}

已有选题池：
${compact(topics || [])}

用户粘贴的历史文案：
${content || ""}

请返回 JSON：
{
  "insights": [
    {"label":"表达风格","title":"...","copy":"..."},
    {"label":"结构习惯","title":"...","copy":"..."},
    {"label":"可优化点","title":"...","copy":"..."}
  ],
  "candidates": [
    {"title":"...","category":"...","reason":"..."}
  ]
}
`;
  return json({ ok: true, ...(await deepseek(env, prompt)) });
}

async function douyinReview(request, env) {
  const { profile, account, raw_data, topics } = await request.json();
  const prompt = `
请基于用户粘贴的抖音创作者数据，做增长复盘。不要假装实时读取抖音，只分析用户提供的数据；如果数据不足，要明确说明。

账号档案：
${compact(profile)}

账号：${account || ""}

选题池：
${compact(topics || [])}

创作者数据：
${raw_data || ""}

请返回 JSON：
{
  "review": {
    "ok": true,
    "account": "...",
    "status": "一句话说明数据来源和可信度",
    "metrics": [{"label":"总播放","value":"..."},{"label":"新增粉丝","value":"..."},{"label":"平均完播","value":"..."},{"label":"内容收入","value":"..."}],
    "videos": [{"title":"...","views":"...","followers":"...","completion":"...","engagement":"...","suggestion":"..."}],
    "diagnosis": [{"title":"涨粉来源","copy":"..."},{"title":"内容优化","copy":"..."},{"title":"下一轮建议","copy":"..."}]
  }
}
`;
  return json({ ok: true, ...(await deepseek(env, prompt)) });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS_HEADERS });
    const url = new URL(request.url);
    try {
      if (request.method !== "POST") return json({ ok: false, error: "Method not allowed" }, 405);
      if (url.pathname === "/api/profile") return profileFeedback(request, env);
      if (url.pathname === "/api/generate-script") return generateScript(request, env);
      if (url.pathname === "/api/analyze-content") return analyzeContent(request, env);
      if (url.pathname === "/api/douyin/sync") return douyinReview(request, env);
      return json({ ok: false, error: "Not found" }, 404);
    } catch (error) {
      return json({ ok: false, error: error.message || "AI service error" }, 500);
    }
  },
};
