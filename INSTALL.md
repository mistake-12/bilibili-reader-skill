# bilibili-reader 接入指南

## 一、接入hermes agent

### 方式一：手动安装到用户skill目录（推荐）

```bash
# 1. 复制整个项目到 ~/.hermes/skills/ 目录
cp -r D:/destop/skill ~/.hermes/skills/bilibili-reader

# 2. 安装Python依赖
cd ~/.hermes/skills/bilibili-reader
pip install -r requirements.txt

# 3. 配置B站Cookie
cp .env.example .env
# 编辑 .env 文件，填入你的B站Cookie
```

### 方式二：放到hermes-agent仓库（贡献为官方skill）

```bash
# 1. 克隆hermes-agent仓库
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 2. 将skill放到optional-skills目录
cp -r D:/destop/skill optional-skills/bilibili-reader

# 3. 提交PR到官方仓库
```

### 方式三：通过hermes CLI安装

```bash
# 从本地路径安装
hermes skills install D:/destop/skill

# 或从GitHub安装（如果已发布）
hermes skills install github:NousResearch/hermes-agent/optional-skills/bilibili-reader
```

---

## 二、配置B站Cookie

### 获取Cookie步骤

1. 打开浏览器，登录 [bilibili.com](https://www.bilibili.com)
2. 按 `F12` 打开开发者工具
3. 点击 `Application`（应用程序）标签
4. 左侧找到 `Cookies` → `https://www.bilibili.com`
5. 复制以下三个值：

| Cookie名称 | 说明 |
|-----------|------|
| `SESSDATA` | 会话数据，用于API认证 |
| `bili_jct` | CSRF令牌 |
| `buvid3` | 设备标识 |

### 配置方式

**方式A：通过hermes交互式配置**

首次使用skill时，hermes会自动提示输入Cookie值。

**方式B：手动创建.env文件**

```bash
cd ~/.hermes/skills/bilibili-reader
cp .env.example .env
```

编辑 `.env` 文件：
```env
BILIBILI_SESSDATA=你的SESSDATA值
BILIBILI_BILI_JCT=你的bili_jct值
BILIBILI_BUVID3=你的buvid3值
```

### Cookie有效期

- B站Cookie通常有效期约30天
- 过期后需要重新获取并更新 `.env` 文件
- 症状：API返回 "请先登录" 或 code=-101

---

## 三、使用方式

### CLI方式

```bash
# 启动hermes
hermes

# 方式1：使用skill命令
> /bilibili-reader

# 方式2：自然语言触发
> 从收藏夹随机选个视频总结一下

# 方式3：直接运行
> 今天推送一个B站视频总结
```

### 消息平台方式（Telegram/Discord等）

```
/bilibili-reader
```

---

## 四、定时任务（Cron）

### 什么是hermes cron？

hermes agent内置了定时任务系统，由gateway的后台线程驱动，**每60秒检查一次**是否有到期任务。任务信息持久化存储在 `~/.hermes/cron/jobs.json` 中。

### 是否需要一直打开hermes？

**是的，hermes需要保持运行状态，cron才会生效。**

具体取决于你的运行方式：

| 运行方式 | 是否需要保持运行 | 推荐程度 | 说明 |
|---------|---------------|---------|------|
| **Docker模式** | 容器在后台运行 | ⭐⭐⭐ 推荐 | `docker compose up -d` 后cron持续生效，关掉终端也不影响 |
| **Serverless模式** | 平台自动管理 | ⭐⭐ | Daytona/Modal按需唤醒，可能有冷启动延迟 |
| **Gateway模式** | 需要保持进程 | ⭐ | 终端关闭后cron停止 |
| **CLI模式** | 交互式运行 | ❌ 不适合 | 仅适合手动触发，不支持定时任务 |

**结论**：如果你需要每天自动推送视频总结，**必须用Docker模式部署hermes**，否则每次都要手动运行。

### Docker部署步骤（推荐）

```bash
# 1. 克隆hermes-agent
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 2. 启动Docker容器（后台运行）
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d

# 3. 查看运行状态
docker compose ps

# 4. 查看日志
docker compose logs -f hermes

# 5. 进入容器配置
docker exec -it hermes bash
```

Docker部署后：
- hermes在后台持续运行
- cron任务每60秒自动检查
- 关掉终端不影响运行
- 重启机器后需要重新 `docker compose up -d`

### 设置cron任务

#### 方式一：通过对话设置

```
hermes
> 设置每天上午9点运行 bilibili-reader skill
```

hermes会自动创建cron任务并保存到 `~/.hermes/cron/jobs.json`。

#### 方式二：使用hermes cron命令

```bash
# 创建定时任务
hermes cron add \
  --name "bilibili-daily" \
  --schedule "0 9 * * *" \
  --skill bilibili-reader

# 查看所有定时任务
hermes cron list

# 删除定时任务
hermes cron remove bilibili-daily

# 手动触发一次（测试用）
hermes cron run bilibili-daily
```

#### 方式三：手动编辑cron配置

编辑 `~/.hermes/cron/jobs.json`：

```json
{
  "jobs": [
    {
      "id": "bilibili-daily",
      "name": "B站视频每日推送",
      "schedule": "0 9 * * *",
      "skill": "bilibili-reader",
      "deliver": "origin",
      "enabled": true
    }
  ]
}
```

### Cron表达式示例

| 表达式 | 含义 |
|-------|------|
| `0 9 * * *` | 每天上午9:00 |
| `0 9 * * 1-5` | 工作日上午9:00 |
| `0 12 * * *` | 每天中午12:00 |
| `0 20 * * 0` | 每周日晚上8:00 |
| `0 9,21 * * *` | 每天上午9点和晚上9点 |
| `0 10 * * *` | 每天上午10:00 |

### 任务执行机制

```
┌─────────────────────────────────────────────┐
│           hermes gateway (Docker)           │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │   cron后台线程（每60秒检查一次）      │   │
│   │                                     │   │
│   │   1. 读取 jobs.json                 │   │
│   │   2. 检查是否有到期任务              │   │
│   │   3. 获取文件锁（防止重复执行）      │   │
│   │   4. 执行 skill                     │   │
│   │   5. 保存输出到 ~/.hermes/cron/     │   │
│   │   6. 推送到配置的消息平台            │   │
│   └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### 任务输出和推送

每次执行后，结果会：
1. 保存到 `~/.hermes/cron/output/<job-id>/` 目录（markdown格式）
2. 推送到配置的消息平台（Telegram/Discord等）

配置推送目标：
```bash
# 推送到Telegram
hermes cron add --name "bilibili-daily" --schedule "0 9 * * *" --skill bilibili-reader --deliver telegram

# 推送到Discord指定频道
hermes cron add --name "bilibili-daily" --schedule "0 9 * * *" --skill bilibili-reader --deliver "discord:-1001:17"

# 仅本地保存，不推送
hermes cron add --name "bilibili-daily" --schedule "0 9 * * *" --skill bilibili-reader --deliver local
```

---

## 五、文件结构说明

```
bilibili-reader/
├── SKILL.md              # skill定义文件（hermes加载入口）
├── INSTALL.md            # 本文件 - 接入指南
├── PRD.md                # 产品需求文档
├── requirements.txt      # Python依赖
├── .env.example          # 环境变量示例
├── .env                  # 实际配置（需手动创建）
├── src/
│   ├── __init__.py
│   ├── __main__.py       # python -m src 入口
│   ├── main.py           # 主流程编排
│   ├── bilibili_api.py   # B站API封装
│   ├── summarizer.py     # LLM总结生成
│   ├── pdf_generator.py  # PDF生成
│   ├── memory.py         # 去重记忆
│   ├── config.py         # 配置管理
│   └── danmaku_pb2.py    # 弹幕protobuf解析
├── templates/
│   └── summary.html      # PDF HTML模板
├── data/
│   └── processed.json    # 已处理视频记录
└── output/               # PDF输出目录
```

---

## 六、常见问题

### Q: skill没有出现在hermes的skill列表中？

```bash
# 检查skill是否正确安装
ls ~/.hermes/skills/bilibili-reader/SKILL.md

# 重新加载skills
hermes skills reload
```

### Q: 如何查看已处理的视频？

```bash
cat ~/.hermes/skills/bilibili-reader/data/processed.json
```

### Q: 如何重置已处理记录？

```bash
# 清空已处理记录
echo '{"processed":[],"stats":{"total_processed":0,"last_processed_at":null}}' > ~/.hermes/skills/bilibili-reader/data/processed.json
```

### Q: PDF中的中文显示为方块？

需要安装中文字体：

```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk

# macOS
brew install --cask font-noto-sans-cjk

# Windows通常自带中文字体，如仍有问题：
# 下载 Noto Sans CJK 并安装到系统字体目录
```

### Q: 如何更新skill？

```bash
# 用新版本覆盖
cp -r D:/destop/skill/* ~/.hermes/skills/bilibili-reader/
```
