if (location.protocol === "file:") {
  location.replace("http://127.0.0.1:8000/");
}

const API_BASE = "";

const state = {
  user: null,
  profile: null,
  topics: [],
  selectedTopicId: "",
  styleSampleCount: 0,
  subscription: null,
  directions: [],
  hotReferences: [],
  importedCandidates: [],
  douyinReview: null,
  usage: null,
  aiProvider: "template",
};

const headerConfig = {
  dashboard: {
    eyebrow: "IP智脑",
    title: "从定位到成稿，把内容生产变成一条清楚的工作流",
    subtitle: "先建立账号定位，再把推荐、爆款、历史文案沉淀成可持续复用的内容资产。",
    action: "开始定位",
    go: "profile",
  },
  profile: {
    eyebrow: "Step 01 · IP 定位",
    title: "先确认你是谁、服务谁、这一阶段要达成什么",
    subtitle: "赛道、目标群体和目标会直接影响推荐方向、爆款参考和后续文案语气。",
    action: "生成推荐",
    go: "discover",
  },
  discover: {
    eyebrow: "Step 02 · 选题推荐",
    title: "根据账号定位，挑出值得进入选题池的方向",
    subtitle: "这里把系统推荐和抖音爆款放在一起，用户只需要选择自己感兴趣的题。",
    action: "去选题池",
    go: "pool",
  },
  pool: {
    eyebrow: "Step 03 · 选题池",
    title: "把所有想拍的内容先沉淀下来，再统一生成文案",
    subtitle: "选题池会成为长期上下文，影响后续脚本结构、表达风格和平台改写。",
    action: "去成稿",
    go: "writer",
  },
  writer: {
    eyebrow: "Step 04 · 文案工坊",
    title: "既能从选题池成稿，也能导入旧内容学习你的风格",
    subtitle: "用户可以粘贴过去的完整文案，系统拆解表达习惯，并把可复用主题回流到选题池。",
    action: "生成文案",
    go: "writer",
  },
  analytics: {
    eyebrow: "Step 05 · 数据复盘",
    title: "先从抖音开始，粘贴数据后由 AI 做复盘建议",
    subtitle: "网页版本不能直接读取另一个网站的登录页面，第一版用复制数据/截图转文字的方式更稳。",
    action: "AI 复盘",
    go: "analytics",
  },
  billing: {
    eyebrow: "订阅",
    title: "低门槛月付，先验证创作者愿不愿意为稳定选题付费",
    subtitle: "9.9 元/月适合作为第一版入口价格，后续可按用量或高级功能分层。",
    action: "查看权益",
    go: "billing",
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const init = {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...options,
  };
  if (init.body && typeof init.body !== "string") {
    init.body = JSON.stringify(init.body);
  }
  const response = await fetch(`${API_BASE}${path}`, init);
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || "请求失败");
    error.data = data;
    throw error;
  }
  return data;
}

function getProfile() {
  return {
    account_name: $("#accountName").value.trim() || "个人 IP 账号",
    niche: $("#niche").value.trim() || "内容增长",
    audience: $("#audience").value.trim() || "目标用户",
    goal: $("#goal").value,
    tone: $("#tone").value.trim() || "清晰、实用",
    advantage: $("#advantage").value.trim() || "能把复杂方法讲简单",
    avoidance: $("#avoidance").value.trim() || "避免空泛表达",
  };
}

function applyProfile(profile) {
  state.profile = profile;
  $("#accountName").value = profile.account_name;
  $("#niche").value = profile.niche;
  $("#audience").value = profile.audience;
  $("#goal").value = profile.goal;
  $("#tone").value = profile.tone;
  $("#advantage").value = profile.advantage;
  $("#avoidance").value = profile.avoidance;
}

function renderAuth() {
  if (!state.user) {
    $("#authStatus").textContent = "未连接";
    return;
  }
  const usageText =
    state.usage && !state.usage.is_paid
      ? ` · AI 剩余 ${state.usage.remaining}/${state.usage.limit}`
      : state.usage?.is_paid
        ? " · 订阅可用"
        : "";
  $("#authStatus").textContent = `${state.user.is_guest ? "访客模式" : state.user.email}${usageText}`;
  $("#logoutBtn").style.display = state.user.is_guest ? "none" : "inline-flex";
}

function setMessage(message, isError = false) {
  $("#authMessage").textContent = message || "";
  $("#authMessage").style.color = isError ? "#ffd3c4" : "#d5ded4";
}

function handleError(error) {
  if (error.data?.usage) {
    state.usage = error.data.usage;
    renderAuth();
  }
  setMessage(error.message, true);
}

function renderProfileSummary() {
  const profile = getProfile();
  $("#personaTitle").textContent = profile.account_name;
  $("#personaSummary").textContent = `一个面向「${profile.audience}」的${profile.niche}型账号，当前目标是${profile.goal}。内容应保持${profile.tone}，核心优势是${profile.advantage}。`;
  $("#workflowProfile").textContent = `${profile.account_name}，面向${profile.audience}，目标是${profile.goal}。`;
  $("#personaPoints").innerHTML = [
    ["赛道", profile.niche],
    ["受众", profile.audience],
    ["目标", profile.goal],
    ["避免", profile.avoidance],
  ]
    .map(
      ([label, value]) => `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `,
    )
    .join("");
}

function renderDirections() {
  const profile = getProfile();
  $("#directionList").innerHTML = state.directions
    .map((item) => {
      const title =
        item.category === "转化销售" ? `围绕「${profile.goal}」设计转化型内容` : item.title;
      return `
        <article class="direction-row">
          <div>
            <div class="tag-row">
              <span class="tag">${escapeHtml(item.category)}</span>
              <span class="tag soft">${escapeHtml(profile.goal)}</span>
            </div>
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(item.angle)}</p>
            <div class="tag-row">
              ${item.formats.map((format) => `<span class="mini-tag">${escapeHtml(format)}</span>`).join("")}
            </div>
          </div>
          <button class="mini-button" data-action="add-direction" data-id="${item.id}">加入选题池</button>
        </article>
      `;
    })
    .join("");
}

function renderHotReferences() {
  $("#hotList").innerHTML = state.hotReferences
    .map(
      (item) => `
        <article class="hot-row">
          <div class="hot-meta">
            <span>${escapeHtml(item.platform)}</span>
            <strong>${escapeHtml(item.views)}</strong>
            <small>播放</small>
          </div>
          <div class="hot-body">
            <div class="tag-row">
              <span class="tag clay">涨粉 ${escapeHtml(item.followers)}</span>
              <span class="tag">${escapeHtml(item.category)}</span>
            </div>
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.reason)}</p>
            <strong class="rewrite-line">可改写：${escapeHtml(item.rewrite)}</strong>
          </div>
          <button class="mini-button" data-action="add-hot" data-id="${item.id}">选择</button>
        </article>
      `,
    )
    .join("");
}

function renderTopics() {
  if (!state.selectedTopicId && state.topics[0]) state.selectedTopicId = state.topics[0].id;
  $("#topicList").innerHTML = state.topics
    .map(
      (topic) => `
        <article class="topic-row ${topic.id === state.selectedTopicId ? "selected" : ""}">
          <div>
            <div class="tag-row">
              <span class="score-pill">${topic.score} 分</span>
              <span class="tag">${escapeHtml(topic.category)}</span>
              <span class="tag soft">${escapeHtml(topic.source)}</span>
            </div>
            <h3>${escapeHtml(topic.title)}</h3>
            <p>${escapeHtml(topic.reason)}</p>
          </div>
          <div class="topic-actions">
            <button class="mini-button" data-action="select-topic" data-id="${topic.id}">选择</button>
            <button class="mini-button" data-action="write-topic" data-id="${topic.id}">成稿</button>
            <button class="mini-button quiet" data-action="delete-topic" data-id="${topic.id}">移除</button>
          </div>
        </article>
      `,
    )
    .join("");

  $("#writerTopicSelect").innerHTML = state.topics
    .map(
      (topic) => `
        <option value="${topic.id}" ${topic.id === state.selectedTopicId ? "selected" : ""}>
          ${escapeHtml(topic.title)}
        </option>
      `,
    )
    .join("");
}

function renderCategoryStack() {
  const groups = state.topics.reduce((acc, topic) => {
    acc[topic.category] = (acc[topic.category] || 0) + 1;
    return acc;
  }, {});
  $("#categoryStack").innerHTML = Object.entries(groups)
    .map(
      ([category, count]) => `
        <div>
          <span>${escapeHtml(category)}</span>
          <strong>${count}</strong>
        </div>
      `,
    )
    .join("");
}

function renderStyleMemory() {
  const profile = getProfile();
  const sampleCopy =
    state.styleSampleCount > 0
      ? `已有 ${state.styleSampleCount} 条风格样本，后续文案会更贴近用户表达。`
      : "还没有保存风格样本，当前先参考 IP 档案和选题池结构。";
  $("#styleMemory").textContent = `${profile.tone}。${sampleCopy}`;
  $("#styleSampleCount").textContent = state.styleSampleCount;
}

function renderStats() {
  $("#topicCount").textContent = state.topics.length;
  $("#scriptReadyCount").textContent = state.topics.length;
  $("#directionCount").textContent = state.directions.length;
  const progress = state.styleSampleCount > 0 ? 100 : state.topics.length > 3 ? 78 : 52;
  $("#sideProgressBar").style.width = `${progress}%`;
  $("#sideProgressTitle").textContent =
    state.styleSampleCount > 0 ? "正在沉淀表达风格" : "正在积累选题池";
  $("#sideProgressCopy").textContent =
    state.styleSampleCount > 0
      ? "已经有风格样本，后续文案会更贴近用户表达。"
      : "选择感兴趣的爆款或方向，进入选题池后再成稿。";
  $("#nextStepCopy").textContent =
    state.topics.length > 3 ? "选题池已经有内容，可以进入文案工坊生成第一条脚本。" : "先从推荐区选择 2-3 个方向进入选题池。";
}

function getSelectedTopic() {
  return state.topics.find((topic) => topic.id === state.selectedTopicId) || state.topics[0];
}

async function addTopic(topic) {
  const data = await api("/api/topics", { method: "POST", body: topic });
  const existingIndex = state.topics.findIndex((item) => item.id === data.topic.id);
  const isDuplicate = existingIndex >= 0 || Boolean(data.duplicate);
  if (existingIndex >= 0) {
    state.topics.splice(existingIndex, 1);
  }
  state.topics.unshift(data.topic);
  state.selectedTopicId = data.topic.id;
  renderAll();
  setMessage(isDuplicate ? "这个选题已在选题池，已帮你选中" : "选题已加入选题池");
  return { topic: data.topic, duplicate: isDuplicate };
}

async function deleteTopic(id) {
  await api(`/api/topics?id=${encodeURIComponent(id)}`, { method: "DELETE" });
  state.topics = state.topics.filter((topic) => topic.id !== id);
  state.selectedTopicId = state.topics[0]?.id || "";
  renderAll();
  setMessage("已移除选题");
}

async function saveProfile() {
  const data = await api("/api/profile", { method: "PUT", body: getProfile() });
  applyProfile(data.profile);
  renderAll();
}

async function renderWriter(seedScript = false) {
  const topic = getSelectedTopic();
  if (!topic) return;
  $("#writerTopicSelect").value = topic.id;
  if (seedScript || !$("#scriptEditor").value.trim()) {
    const data = await api("/api/generate-script", {
      method: "POST",
      body: { topic_id: topic.id, format: $("#scriptFormat").value },
    });
    $("#scriptEditor").value = data.script;
    state.usage = data.usage || state.usage;
    renderAuth();
    setMessage("已生成文案草稿");
  }
  renderPlatformVersions();
}

function renderPlatformVersions() {
  const topic = getSelectedTopic();
  if (!topic) return;
  const profile = getProfile();
  $("#platformVersions").innerHTML = [
    {
      name: "抖音口播",
      copy: `开头直接抛痛点：${topic.title}。中段给 3 个步骤，结尾引导评论关键词。`,
    },
    {
      name: "小红书图文",
      copy: `封面突出结果，正文用清单结构拆解「${topic.category}」，每段控制在 2-3 行。`,
    },
    {
      name: "公众号开头",
      copy: `从${profile.audience}的真实困境切入，再过渡到账号方法论和完整案例。`,
    },
  ]
    .map(
      (item) => `
        <article class="platform-row">
          <strong>${escapeHtml(item.name)}</strong>
          <p>${escapeHtml(item.copy)}</p>
        </article>
      `,
    )
    .join("");
}

function formatViews(value) {
  const number = Number(value);
  if (Number.isFinite(number)) return `${(number / 10000).toFixed(1)} 万播放`;
  return escapeHtml(value || "-");
}

function formatPercent(value) {
  if (value === undefined || value === null || value === "") return "-";
  return String(value).includes("%") ? escapeHtml(value) : `${escapeHtml(value)}%`;
}

async function analyzeImportedContent() {
  const content = $("#importedContent").value.trim();
  if (!content) {
    $("#importInsights").innerHTML = `
      <article class="import-card">
        <strong>等待内容</strong>
        <p>把用户过去写过的一组完整文案粘贴进来后，这里会拆解风格、结构和可回流选题。</p>
      </article>
    `;
    setMessage("先粘贴一组完整内容", true);
    return;
  }
  const data = await api("/api/analyze-content", { method: "POST", body: { content } });
  state.styleSampleCount = data.style_sample_count;
  state.importedCandidates = data.candidates || [];
  state.usage = data.usage || state.usage;
  $("#importInsights").innerHTML = `
    ${data.insights
      .map(
        (item) => `
          <article class="import-card">
            <span>${escapeHtml(item.label)}</span>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.copy)}</p>
          </article>
        `,
      )
      .join("")}
    <article class="import-card wide-import">
      <span>可回流选题</span>
      <div class="import-topic-list">
        ${state.importedCandidates
          .map(
            (theme, index) => `
              <button class="import-topic-button" data-action="add-imported-topic" data-index="${index}">
                ${escapeHtml(theme.title)}
              </button>
            `,
          )
          .join("")}
      </div>
    </article>
  `;
  setMessage("已拆解历史文案，并生成可回流选题");
  renderStats();
  renderStyleMemory();
  renderAuth();
}

function renderDouyinReview(review) {
  state.douyinReview = review || state.douyinReview;
  if (!state.douyinReview) return;
  $("#syncStatus").textContent = state.douyinReview.status;
  $("#douyinMetrics").innerHTML = state.douyinReview.metrics
    .map(
      (item) => `
        <div>
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
        </div>
      `,
    )
    .join("");
  $("#douyinVideoList").innerHTML = state.douyinReview.videos
    .map(
      (video) => `
        <article class="douyin-video-row">
          <div>
            <h3>${escapeHtml(video.title)}</h3>
            <p>${escapeHtml(video.suggestion)}</p>
          </div>
          <div class="video-stats">
            <span>${formatViews(video.views)}</span>
            <span>涨粉 ${escapeHtml(video.followers ?? "-")}</span>
            <span>完播 ${formatPercent(video.completion)}</span>
            <span>互动 ${formatPercent(video.engagement)}</span>
          </div>
        </article>
      `,
    )
    .join("");
  $("#diagnosis").innerHTML = state.douyinReview.diagnosis
    .map(
      (item) => `
        <article class="diagnosis-row">
          <strong>${escapeHtml(item.title)}</strong>
          <p>${escapeHtml(item.copy)}</p>
        </article>
      `,
    )
    .join("");
}

async function syncDouyin() {
  const data = await api("/api/douyin/sync", {
    method: "POST",
    body: { account: $("#douyinAccount").value.trim(), raw_data: $("#douyinRawData").value.trim() },
  });
  state.usage = data.usage || state.usage;
  renderDouyinReview(data);
  renderAuth();
  setMessage("抖音数据已同步");
}

async function checkout() {
  const data = await api("/api/checkout", { method: "POST", body: { plan: "creator-monthly" } });
  state.subscription = data.subscription;
  $("#checkoutNote").textContent = data.message;
  setMessage("订阅状态已更新");
}

function updateHeader(viewId) {
  const config = headerConfig[viewId] || headerConfig.dashboard;
  $("#headerEyebrow").textContent = config.eyebrow;
  $("#headerTitle").textContent = config.title;
  $("#headerSubtitle").textContent = config.subtitle;
  $("#headerAction").textContent = config.action;
  $("#headerAction").dataset.headerAction = viewId;
}

function showView(viewId) {
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === viewId));
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === viewId));
  updateHeader(viewId);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function handleHeaderAction(viewId) {
  if (viewId === "dashboard") showView("profile");
  if (viewId === "profile") {
    await saveProfile();
    showView("discover");
  }
  if (viewId === "discover") showView("pool");
  if (viewId === "pool") {
    await renderWriter(true);
    showView("writer");
  }
  if (viewId === "writer") await renderWriter(true);
  if (viewId === "analytics") await syncDouyin();
  if (viewId === "billing") await checkout();
}

function renderAll() {
  renderAuth();
  renderProfileSummary();
  renderDirections();
  renderHotReferences();
  renderTopics();
  renderCategoryStack();
  renderStyleMemory();
  renderStats();
  renderPlatformVersions();
}

async function bootstrap() {
  try {
    const data = await api("/api/bootstrap");
    state.user = data.user;
    state.topics = data.topics || [];
    state.selectedTopicId = state.topics[0]?.id || "";
    state.styleSampleCount = data.style_sample_count || 0;
    state.subscription = data.subscription;
    state.usage = data.usage;
    state.aiProvider = data.ai_provider || "template";
    state.directions = data.directions || [];
    state.hotReferences = data.hot_references || [];
    applyProfile(data.profile);
    renderAll();
    updateHeader("dashboard");
    setMessage(state.user.is_guest ? "访客数据已保存到本机服务" : "已登录");
  } catch (error) {
    $("#authStatus").textContent = "未连接服务";
    setMessage("请通过本地服务地址打开页面", true);
    console.error(error);
  }
}

function bindEvents() {
  $$(".nav-item").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });

  document.addEventListener("click", async (event) => {
    const action = event.target.dataset.action;
    const id = event.target.dataset.id;
    const go = event.target.dataset.go;
    const headerAction = event.target.dataset.headerAction;
    try {
      if (headerAction) {
        await handleHeaderAction(headerAction);
        return;
      }

      if (go) {
        if (go === "writer") await renderWriter(false);
        if (go === "analytics") await syncDouyin();
        showView(go);
      }

      if (action === "add-direction") {
        const item = state.directions.find((direction) => direction.id === id);
        if (!item) return;
        await addTopic({
          title: `${item.title}：给${getProfile().audience}的 3 个具体方法`,
          category: item.category,
          source: "方向推荐",
          reason: item.angle,
          reference: item.formats.join(" / "),
        });
        showView("pool");
      }

      if (action === "add-hot") {
        const item = state.hotReferences.find((reference) => reference.id === id);
        if (!item) return;
        await addTopic({
          title: item.rewrite,
          category: item.category,
          source: "抖音爆款",
          reason: item.reason,
          reference: `${item.title}，播放 ${item.views}，涨粉 ${item.followers}`,
        });
        showView("pool");
      }

      if (action === "select-topic") {
        state.selectedTopicId = id;
        renderAll();
        setMessage("已选择这个选题");
      }

      if (action === "write-topic") {
        state.selectedTopicId = id;
        renderAll();
        await renderWriter(true);
        showView("writer");
      }

      if (action === "delete-topic") await deleteTopic(id);

      if (action === "add-imported-topic") {
        const item = state.importedCandidates[Number(event.target.dataset.index)];
        if (!item) return;
        const result = await addTopic({
          title: item.title,
          category: item.category,
          source: "历史文案拆解",
          reason: item.reason,
          reference: "来自用户导入的历史文案",
        });
        if (!result.duplicate) setMessage("历史文案选题已回流到选题池");
        showView("pool");
      }
    } catch (error) {
      handleError(error);
    }
  });

  ["accountName", "niche", "audience", "goal", "tone", "advantage", "avoidance"].forEach((id) => {
    $(`#${id}`).addEventListener("input", renderAll);
    $(`#${id}`).addEventListener("change", renderAll);
  });

  $("#saveProfileBtn").addEventListener("click", async () => {
    try {
      await saveProfile();
      showView("discover");
    } catch (error) {
      handleError(error);
    }
  });

  $("#refreshRecommendationsBtn").addEventListener("click", () => {
    renderDirections();
    setMessage("推荐已刷新");
  });

  $("#addManualTopicBtn").addEventListener("click", async () => {
    const title = $("#manualTopic").value.trim();
    if (!title) {
      setMessage("先输入一个选题标题", true);
      return;
    }
    await addTopic({
      title,
      category: $("#topicCategory").value,
      source: "手动添加",
      reason: "由用户主动添加，后续文案会参考账号定位和选题池上下文。",
      reference: "用户自定义选题",
    });
    $("#manualTopic").value = "";
  });

  $("#writerTopicSelect").addEventListener("change", async (event) => {
    state.selectedTopicId = event.target.value;
    renderAll();
    await renderWriter(true);
  });

  $("#generateScriptBtn").addEventListener("click", async () => {
    try {
      await renderWriter(true);
    } catch (error) {
      handleError(error);
    }
  });

  $("#saveStyleBtn").addEventListener("click", async () => {
    const content = $("#scriptEditor").value.trim();
    if (!content) return;
    const data = await api("/api/style-samples", { method: "POST", body: { content } });
    state.styleSampleCount = data.style_sample_count;
    renderAll();
    setMessage("已保存为风格样本");
  });

  $("#convertPlatformsBtn").addEventListener("click", () => {
    renderPlatformVersions();
    setMessage("已生成平台版本");
  });
  $("#analyzeImportBtn").addEventListener("click", async () => {
    try {
      await analyzeImportedContent();
    } catch (error) {
      handleError(error);
    }
  });
  $("#syncDouyinBtn").addEventListener("click", async () => {
    try {
      await syncDouyin();
    } catch (error) {
      handleError(error);
    }
  });
  $("#checkoutBtn").addEventListener("click", async () => {
    try {
      await checkout();
    } catch (error) {
      handleError(error);
    }
  });

  $("#registerBtn").addEventListener("click", async () => {
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: { email: $("#authEmail").value, password: $("#authPassword").value },
      });
      setMessage("注册成功");
      await bootstrap();
    } catch (error) {
      handleError(error);
    }
  });

  $("#loginBtn").addEventListener("click", async () => {
    try {
      await api("/api/auth/login", {
        method: "POST",
        body: { email: $("#authEmail").value, password: $("#authPassword").value },
      });
      setMessage("登录成功");
      await bootstrap();
    } catch (error) {
      setMessage(error.message, true);
    }
  });

  $("#logoutBtn").addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST", body: {} });
    setMessage("已退出");
    await bootstrap();
  });
}

bindEvents();
analyzeImportedContent();
bootstrap();
