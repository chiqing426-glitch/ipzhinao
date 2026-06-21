# IP智脑

IP智脑是面向自媒体博主和个人 IP 的内容工作台 MVP。

当前能力：

- 邮箱注册、登录、退出
- IP 定位：赛道、受众、目标、表达风格
- 方向推荐和爆款参考
- 选题池保存和手动添加
- 文案工坊：生成文案、拆解旧文案、沉淀风格样本
- 抖音数据复盘：用户粘贴创作者数据后由 AI 给出建议
- 免费用户 3 次 AI 使用额度
- 9.9 元/月订阅状态预留

## 本地启动

```bash
python server.py
```

访问：

```text
http://127.0.0.1:8000/
```

## Railway 环境变量

```text
HOST=0.0.0.0
FREE_AI_LIMIT=3
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_MODEL=deepseek-v4-flash
DB_PATH=/data/app.db
```
