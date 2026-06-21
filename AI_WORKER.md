# IP智脑 AI 后端

当前 GitHub Pages 版本支持两种模式：

- 没有 AI 后端：使用浏览器本地测试反馈，适合看流程。
- 配置 AI 后端：调用 Cloudflare Worker，再由 Worker 安全调用 DeepSeek。

## 需要的密钥

Cloudflare Worker 需要设置 Secret：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

可选变量：

```text
DEEPSEEK_MODEL=deepseek-chat
```

## 部署后连接前端

Worker 部署成功后，会得到类似：

```text
https://ipzhinao-ai.xxx.workers.dev
```

第一次打开前端时带上参数：

```text
https://chiqing426-glitch.github.io/ipzhinao/?ai=https://ipzhinao-ai.xxx.workers.dev
```

浏览器会记住这个 AI 地址，之后直接打开普通链接也会继续使用真实 AI。

## 当前 AI 接口

- `POST /api/profile`：IP 定位反馈、选题方向、爆款结构参考
- `POST /api/generate-script`：完整文案生成
- `POST /api/analyze-content`：历史文案拆解和回流选题
- `POST /api/douyin/sync`：粘贴数据后的复盘建议
