<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/LLM-OpenAI_Compatible-FF6F00?style=for-the-badge&logo=openai&logoColor=white" alt="LLM">
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/ZpjDev/Hotel-AI-Housemaster?style=social" alt="GitHub stars">
  <img src="https://img.shields.io/github/forks/ZpjDev/Hotel-AI-Housemaster?style=social" alt="GitHub forks">
  <img src="https://img.shields.io/github/last-commit/ZpjDev/Hotel-AI-Housemaster?style=social" alt="Last commit">
</p>

<h1 align="center">Hotel AI Housemaster</h1>

<p align="center">
  <b>酒店 / 民宿 AI 智能管家系统</b><br/>
  <sub>为中小酒店和民宿提供一站式 AI 经营管理解决方案</sub>
</p>

---

## 项目简介

**Hotel AI Housemaster** 是一个基于 FastAPI 构建的酒店 AI 经营助手，深度集成了大语言模型（LLM），打通了从**经营数据分析 → AI 策略生成 → 多平台执行 → 效果反馈**的完整闭环。

老板只需在微信上发一条消息，AI 管家就能告诉你今晚该定什么价、竞品在做什么、哪里需要调整 —— 就像一个 24 小时在线的专业酒店总经理。

### 解决的核心问题

| 痛点 | 传统方式 | AI 管家方案 |
|------|---------|------------|
| 定价靠经验 | 老板凭感觉调价 | 数据驱动 + LLM 分析，实时推荐最优价格区间 |
| 竞品看不见 | 手动去 OTA 平台翻 | 自动多源同步，价格变动一目了然 |
| 差评回复慢 | 想半天不知道怎么回 | 按评分分级生成得体回复，一键可用 |
| 月报不会写 | 数据散落各处，手动汇总 | 自动拉取全月数据，AI 生成专业报告 |
| 不在店管不了 | 人不在就只能靠电话问 | 微信随时随地获取经营建议 |

---

## 技术栈

### 后端核心

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.5+-E92063?style=flat-square&logo=pydantic&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLModel-0.0.14+-FF6F00?style=flat-square&logo=sqlalchemy&logoColor=white)

### 数据库 & 存储

![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-003B57?style=flat-square&logo=sqlite&logoColor=white)

### AI & LLM

![OpenAI](https://img.shields.io/badge/LLM-OpenAI_Compatible-412991?style=flat-square&logo=openai&logoColor=white)
![Qwen](https://img.shields.io/badge/默认模型-通义千问_qwen--turbo-615eed?style=flat-square)

### 定时任务 & 异步

![APScheduler](https://img.shields.io/badge/APScheduler-3.10+-00BFFF?style=flat-square)
![HTTPX](https://img.shields.io/badge/HTTPX-0.25+-2C3E50?style=flat-square)

### 前端

![Jinja2](https://img.shields.io/badge/Jinja2-3.1+-B41717?style=flat-square&logo=jinja&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-后台管理-E34F26?style=flat-square&logo=html5&logoColor=white)

### 部署 & DevOps

![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat-square&logo=docker&logoColor=white)
![docker-compose](https://img.shields.io/badge/docker--compose-Supported-2496ED?style=flat-square&logo=docker&logoColor=white)
![微信云托管](https://img.shields.io/badge/微信云托管-Ready-07C160?style=flat-square&logo=wechat&logoColor=white)

### 集成

![企业微信](https://img.shields.io/badge/企业微信-Webhook-07C160?style=flat-square&logo=wechat&logoColor=white)
![OTA](https://img.shields.io/badge/OTA-多源同步-FF6600?style=flat-square)

---

## 系统架构

```text
                          ┌─────────────────────────────────┐
                          │          微信 / 企业微信           │
                          │      老板用微信对话查询经营          │
                          └──────────────┬──────────────────┘
                                         │ Webhook
                                         ▼
┌──────────────┐    同步竞品价格    ┌──────────────┐     AI 分析    ┌──────────────┐
│   OTA 平台    │ ◄─────────────── │              │ ────────────── │   大语言模型   │
│ (携程/美团等)  │ ───────────────► │  Hotel AI    │ ◄────────────── │ (通义千问/    │
│              │    dry-run 测试   │ Housemaster  │    结构化 JSON  │  GPT-4等)    │
└──────────────┘                  │  (FastAPI)   │                └──────────────┘
                                  │              │
┌──────────────┐                   │              │                 ┌──────────────┐
│   电话 API    │ ◄─────────────── │              │ ─────────────── │  Webhook     │
│ (阿里云/腾讯)  │    AI 接听回复    └──────┬───────┘   通知推送      │  通知 (钉钉/  │
└──────────────┘                          │                        │  飞书/企业微信) │
                                          ▼                        └──────────────┘
                                 ┌────────────────┐
                                 │   SQLite 数据库  │
                                 │  (可按需换 PG)   │
                                 └────────────────┘
```

---

## 功能矩阵

### 业务管理 — 酒店经营的基础数据

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/hotels` | GET / POST | 酒店列表 / 新增酒店 |
| `/api/hotels/{id}` | GET / PUT | 酒店详情 / 更新信息 |
| `/api/room-types` | POST | 新增房型（含基础价、价格区间、配置） |
| `/api/hotels/{id}/room-types` | GET | 房型列表 |
| `/api/room-types/{id}` | PUT | 更新房型信息 |
| `/api/daily-business` | POST | 录入每日经营数据（售房数、营收等） |
| `/api/hotels/{id}/daily-business` | GET | 按日期范围查询经营数据 |
| `/api/competitors` | POST | 添加竞品酒店 |
| `/api/hotels/{id}/competitors` | GET | 竞品列表 |
| `/api/competitor-prices` | POST | 录入竞品价格 |
| `/api/competitors/{id}/prices` | GET | 竞品价格查询 |

### AI 策略 — LLM 驱动的智能分析

```
POST /api/ai/strategy
```

输入：酒店 ID、目标日期、可选的问题

输出（强制 JSON 结构）：

```json
{
  "market_analysis":          "当前整体市场需求判断",
  "competitor_analysis":      "竞品价格区间与房态对比",
  "suggested_prices": [
    {
      "room_type": "豪华大床房",
      "min_price": 388,
      "max_price": 428,
      "reason": "定价理由"
    }
  ],
  "suggested_price":          "综合建议价格区间",
  "room_control_strategy":    "如何分配房间库存",
  "ota_strategy":             "OTA 平台操作建议",
  "promotion_strategy":       "是否或如何做促销活动",
  "direct_customer_strategy": "如何引导直客下单",
  "risk_alert":               "潜在风险预警",
  "actions_required": [
    {
      "action": "具体操作描述",
      "type": "pricing",
      "reason": "执行原因"
    }
  ],
  "full_report":              "完整 Markdown 策略报告"
}
```

> `suggested_prices` 为每个房型给出建议价格区间；`actions_required` 列出需要人工确认的高风险操作（type 可选值：`pricing` `inventory` `order` `promotion`）。

> **Fallback 机制**：LLM 调用失败或 JSON 解析失败时，自动降级为规则引擎策略（基于入住率阈值），确保系统始终可用。

**其他 AI 能力：**

| 接口 | 说明 |
|------|------|
| `POST /api/reports/monthly` | 月度经营报告（营收、ADR、RevPAR、竞品对比、渠道分析、下月建议） |
| `POST /api/reviews/{id}/reply` | 点评智能回复（1-5 分分级策略，语气真诚专业） |
| `POST /api/ai/customer-question-reply` | 客户问题自动回复（基于酒店知识库） |

### 竞品监测 — 多源数据同步

```
POST /api/external/competitor-sync
```

支持 4 种数据源，可按需切换：

| Provider | 说明 | 用途 |
|----------|------|------|
| `mock` | 模拟数据生成器 | 开发 / 演示 / fallback |
| `manual` | 人工录入 | 无 API 可用的竞品 |
| `third_party` | 第三方数据服务商 | 通过 HTTP API 获取 |
| `official` | OTA 官方 API | 如携程开放平台 |

**容错设计**：任意外部 Provider 失败时自动 fallback 到 `mock`，不影响业务流程。每次调用均记录到 `api_logs` 表。

**Dry-run 模式**（调试用）：

```bash
curl -X POST http://localhost:8000/api/external/ota-dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_id": 1,
    "competitor_id": 1,
    "target_date": "2026-05-10",
    "provider": "third_party"
  }'
```

调用真实 API，返回映射结果但不写入数据库。

### 微信接入 — 老板的移动管家

```
GET  /wechat/webhook    # Token 校验
POST /wechat/webhook    # 消息接收与回复
```

老板通过微信发送消息，AI 自动识别意图并响应：

| 你发的消息 | AI 识别意图 | 返回内容 |
|-----------|------------|---------|
| "今晚定什么价" | `pricing` | 基于入住率和竞品数据的实时定价建议 |
| "还有多少空房" | `room_status` | 当前房态统计 |
| "竞品什么价" | `competitor` | 周边竞品价格区间对比 |
| "给个完整策略" | `strategy` | 完整 JSON 策略报告 |
| "这个月报告" | `monthly_report` | 月度经营分析报告 |
| "你好" | `greeting` | 自然语言对话 |

### 定时任务 — 自动化的经营节奏

每日 5 个时段自动执行（通过 APScheduler）：

| 时段 | 时间 | 操作 |
|------|------|------|
| 早间 | 09:00 | 同步竞品数据 + 生成早间策略 |
| 午间 | 12:00 | 同步竞品数据 + 生成午间策略 |
| 午后 | 16:00 | 同步竞品数据 + 生成下午策略 |
| 晚间 | 18:00 | 同步竞品数据 + 生成晚间策略 |
| 夜间 | 22:00 | 同步竞品数据 + 生成夜间策略（尾房处理） |

每次执行：自动拉取竞品最近 30 天价格 → 生成结构化 AI 策略 → 保存报告 → 微信推送老板。

### 后台管理 — Web 可视化面板

| 页面 | 路由 | 功能 |
|------|------|------|
| 首页 | `/admin` | 酒店列表总览 |
| 竞品管理 | `/admin/hotels/{id}/competitors` | 添加/查看竞品 |
| 房型管理 | `/admin/hotels/{id}/room-types` | 房型 CRUD |
| 房态日历 | `/admin/hotels/{id}/room-calendar` | 月度日历视图，入住率热力图 |
| 订单管理 | `/admin/hotels/{id}/orders` | OTA 订单列表 |
| API 配置 | `/admin/api-settings` | 所有外部 API 在线配置 + 连接测试 |
| 待审批 | `/admin/pending-actions` | AI 建议的高风险操作审批 |
| 系统设置 | `/admin/settings` | API 配置速览 |
| 系统监控 | `/admin/monitor` | 调用统计、错误追踪 |

### 系统监控 — 健康与可观测性

| 接口 | 说明 |
|------|------|
| `GET /monitor/stats` | 系统整体统计（请求量、成功率、延迟分布） |
| `GET /monitor/providers` | 各 Provider 成功率与延迟 |
| `GET /monitor/health` | 各组件健康检查 |
| `GET /monitor/errors` | 最近错误列表 |
| `GET /monitor/timeline` | API 调用时间线 |
| `GET /api/api-logs` | 按 Provider / 状态筛选调用日志 |

---

## 数据模型

```text
Hotel ─────────── 酒店基本信息（名称、地址、房量等）
  ├── RoomType ── 房型（名称、基础价、价格范围、配置）
  ├── DailyBusiness ── 每日经营（入住率、ADR、RevPAR、营收）
  ├── CompetitorHotel ── 竞品酒店
  │     └── CompetitorPrice ── 竞品每日价格
  ├── StrategyReport ── AI 策略报告（JSON 结构化）
  ├── Customer ── 客户信息
  ├── Review ── 客户评价（含 AI 回复）
  ├── OTAOrder ── OTA 订单
  ├── PendingAction ── 待人工审批的操作
  ├── KnowledgeBase ── 酒店 FAQ 知识库
  └── APIConfig ── 外部 API 配置（加密存储）
       └── APILog ── API 调用审计日志
```

---

## 配置架构

```
┌─────────────────────────────────┐
│         请求配置值                │
└───────────────┬─────────────────┘
                ▼
┌─────────────────────────────────┐
│   api_configs 表（数据库）        │  ← 优先：后台页面在线修改，加密存储
│   /admin/api-settings           │
└───────────────┬─────────────────┘
                │ 表中无值时 fallback
                ▼
┌─────────────────────────────────┐
│   .env 环境变量                  │  ← 兜底：部署时配置
└─────────────────────────────────┘
```

支持的配置项：
`ai_api_base` | `ai_api_key` | `ai_model` | `ota_api_base` | `ota_api_key` | `wechat_token` | `wechat_encoding_aes_key` | `wechat_app_id` | `wechat_app_secret` | `phone_api_base` | `phone_api_key` | `notify_webhook_url`

> 敏感值采用加密存储，后台管理页显示脱敏后的值（如 `sk-a****b1c2`），永不明文返回。

---

## 快速开始

### 环境要求

- Python 3.9+
- （可选）Docker & docker-compose

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/ZpjDev/Hotel-AI-Housemaster.git
cd Hotel-AI-Housemaster

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 AI_API_KEY 等信息

# 4. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker 运行

```bash
docker-compose up -d
```

### 访问

| 入口 | 地址 |
|------|------|
| API 文档 (Swagger UI) | http://localhost:8000/docs |
| 后台管理面板 | http://localhost:8000/admin |
| 健康检查 | http://localhost:8000/health |

---

## 项目目录

```text
hotel_ai_butler/
├── app/
│   ├── main.py                      # FastAPI 应用入口（路由注册、生命周期）
│   ├── config.py                    # 环境变量配置（pydantic-settings）
│   ├── database.py                  # SQLModel 引擎 + 会话依赖注入
│   ├── models/__init__.py           # 全部 11 个数据模型
│   ├── schemas/__init__.py          # Pydantic 请求/响应 Schema
│   ├── routers/
│   │   ├── business.py              # 酒店、房型、经营数据、竞品 CRUD
│   │   ├── ai.py                    # AI 策略、月度报告、点评回复
│   │   ├── management.py            # 客户、点评、订单、审批、配置、知识库
│   │   ├── external.py              # OTA 竞品同步 + dry-run
│   │   ├── wechat.py                # 微信 Webhook
│   │   ├── admin.py                 # 后台管理 9 个 HTML 页面
│   │   ├── api_logs.py              # API 调用日志查询
│   │   └── monitor.py               # 系统监控 API
│   ├── services/
│   │   ├── ai_provider.py           # LLM 调用（retry + fallback + 加密）
│   │   ├── strategy_service.py      # 策略生成（JSON 输出 + 规则引擎 fallback）
│   │   ├── report_service.py        # 月度报告生成
│   │   ├── scheduler_service.py     # 5 时段定时任务调度
│   │   ├── system_monitor.py        # 系统监控服务
│   │   ├── crud_*.py                # 各模块数据库操作
│   │   ├── external_api/            # OTA 数据源 Provider（5 个实现）
│   │   ├── wechat/                  # 微信服务（消息处理、公众号 API）
│   │   └── phone/                   # 电话服务（阿里云/腾讯云/Mock）
│   ├── templates/admin/             # 9 个后台管理 HTML 模板
│   └── utils/api_log.py             # API 调用日志记录
├── scripts/
│   ├── build_release.py             # 发布包生成
│   ├── configure_wechat.py          # 微信配置向导
│   ├── wechat_one_click_setup.py    # 微信一键配置
│   ├── run_wechat_ai_bridge.py      # 微信 AI 桥接测试
│   └── migrate_add_competitor_price_fields.py  # 数据库迁移脚本
├── Dockerfile                       # Docker 镜像（微信云托管兼容 80 端口）
├── docker-compose.yml               # 本地 Docker 编排
├── container.config.json            # 微信云托管配置
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
└── README.md
```

---

## 开发计划

- [x] 核心业务 CRUD + 竞品管理
- [x] LLM 策略生成（强制 JSON + 规则引擎 fallback）
- [x] 月度报告 AI 生成
- [x] 点评 AI 自动回复（分级策略）
- [x] 微信企业号 / 公众号 Webhook 接入
- [x] 多源 OTA 数据 Provider（mock / manual / third_party / official）
- [x] 定时任务调度（每日 5 时段）
- [x] 后台管理 Web 面板（9 页面）
- [x] 待确认动作审批流程
- [x] 系统监控 + API 调用日志
- [x] 配置加密存储
- [ ] PostgreSQL / MySQL 数据库支持
- [ ] 前端 SPA 重构（React / Vue）
- [ ] 多租户 SaaS 化
- [ ] 钉钉 / 飞书渠道接入
- [ ] 多语言支持

---

## License

MIT License — 可自由使用、修改和商用。
