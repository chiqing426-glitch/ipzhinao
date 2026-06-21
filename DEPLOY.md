# IP智脑上线清单

## 1. 当前版本能力

- 产品名：IP智脑
- 域名建议：`ipzhinao.cn` 或 `ipzhinao.com`
- 账号：邮箱注册、登录、退出
- 数据：用户档案、选题池、历史文案样本、订阅状态、AI 使用次数保存在 SQLite 数据库
- AI：通过 DeepSeek API 生成文案、拆解历史文案、复盘抖音数据
- 免费额度：每个用户 3 次 AI 使用
- 订阅：预留 9.9 元/月状态，支付通道待接入

## 2. 抖音数据复盘方案

纯网页不能直接读取用户另一个标签页里的抖音创作者服务中心数据，也不能绕过登录态、验证码、反爬或浏览器安全限制。

第一版采用可上线方案：

1. 用户自己登录抖音创作者服务中心。
2. 用户复制最近 7 天或 30 天核心数据，粘贴到 IP智脑的数据复盘区。
3. IP智脑调用 DeepSeek 做增长诊断和下一轮选题建议。

后续全自动方案有两条：

- 浏览器插件：用户授权插件读取当前抖音页面可见数据，再传回 IP智脑。
- 桌面助手：用户本机授权后由本地助手截图/识别，再传回 IP智脑。

## 3. DeepSeek 配置

服务器环境变量：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
export DEEPSEEK_MODEL="deepseek-v4-flash"
export FREE_AI_LIMIT="3"
export HOST="0.0.0.0"
export PORT="8000"
```

本地没有 `DEEPSEEK_API_KEY` 时，系统会使用模板降级，方便调试。

## 4. 国内云服务器建议

建议先用腾讯云轻量应用服务器：

- 地域：上海、广州、北京都可以
- 系统：Ubuntu 22.04 LTS 或 Ubuntu 24.04 LTS
- 配置：2 核 2G 起步，带宽 3Mbps 起步
- 数据库：第一版继续 SQLite，数据库文件在 `content-ip-app/data/app.db`

上线后再根据用户量迁移到 MySQL 或 PostgreSQL。

## 5. 服务器部署命令

把 `content-ip-app` 上传到服务器后：

```bash
cd /opt/ipzhinao/content-ip-app
mkdir -p data
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
export HOST="0.0.0.0"
export PORT="8000"
python3 server.py
```

浏览器访问：

```text
http://服务器公网IP:8000/
```

## 6. systemd 常驻服务

创建文件：

```bash
sudo nano /etc/systemd/system/ipzhinao.service
```

内容：

```ini
[Unit]
Description=IP智脑 Web App
After=network.target

[Service]
WorkingDirectory=/opt/ipzhinao/content-ip-app
Environment=HOST=0.0.0.0
Environment=PORT=8000
Environment=FREE_AI_LIMIT=3
Environment=DEEPSEEK_MODEL=deepseek-v4-flash
Environment=DEEPSEEK_API_KEY=替换成你的Key
ExecStart=/usr/bin/python3 /opt/ipzhinao/content-ip-app/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ipzhinao
sudo systemctl start ipzhinao
sudo systemctl status ipzhinao
```

## 7. Nginx 和域名

安装 Nginx：

```bash
sudo apt update
sudo apt install -y nginx
```

站点配置：

```bash
sudo nano /etc/nginx/sites-available/ipzhinao
```

内容：

```nginx
server {
    listen 80;
    server_name ipzhinao.cn www.ipzhinao.cn;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/ipzhinao /etc/nginx/sites-enabled/ipzhinao
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS

备案通过、域名解析到服务器后，再配置 HTTPS：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ipzhinao.cn -d www.ipzhinao.cn
```

## 9. 备案流程

国内服务器正式绑定域名访问前，需要 ICP 备案。

建议同一家云服务商完成三件事：

1. 买云服务器。
2. 买域名并完成实名认证。
3. 在云服务商备案系统提交 ICP 备案。

备案通常需要准备：

- 身份证或营业执照
- 手机号、邮箱、通信地址
- 域名实名认证信息
- 云服务器备案资源
- 网站名称：IP智脑
- 网站服务内容：工具/内容创作辅助/信息服务，按云服务商页面可选项填写

腾讯云首次备案流程大致是：

1. 验证备案类型
2. 填写主体信息
3. 填写网站和域名信息
4. 上传补充材料
5. 提交腾讯云初审
6. 完成短信核验
7. 等待管局审核

备案通过后，把备案号放到网页底部。

## 10. 下一步待接

- 微信支付或支付宝订阅
- 备案号展示
- 隐私政策、用户协议、退款说明
- 数据库每日备份
- 管理后台
