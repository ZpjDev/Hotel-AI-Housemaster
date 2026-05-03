# 酒店/民宿 AI 智能管家系统

这是一个基于 FastAPI 的酒店/民宿经营助手后端，提供经营分析、竞品监测、AI 定价、月报、点评回复、微信 webhook、后台管理和外部 API 配置能力。

## 交付范围

- 酒店、房型、经营数据、竞品数据、客户、点评、订单管理
- AI 经营策略与月度报告
- 微信 webhook 接入与客服消息发送
- OTA 数据同步与 dry-run 校验
- API 配置后台与调用日志
- 待确认动作审批页

## 目录结构

```text
app/
  config.py
  database.py
  main.py
  models/
  routers/
  schemas/
  services/
  templates/
scripts/
  build_release.py
  configure_wechat.py
  migrate_add_competitor_price_fields.py
  run_wechat_ai_bridge.py
  wechat_one_click_setup.py
Dockerfile
docker-compose.yml
requirements.txt
```

## 部署准备

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量，或在后台 API 设置页写入配置

建议至少配置以下项目：

- `AI_API_BASE`
- `AI_API_KEY`
- `AI_MODEL`
- `WECHAT_APP_ID`
- `WECHAT_APP_SECRET`
- `WECHAT_TOKEN`
- `WECHAT_ENCODING_AES_KEY`
- `OTA_API_BASE`
- `OTA_API_KEY`

3. 如需补充 OTA 字段，执行迁移脚本

```bash
python scripts/migrate_add_competitor_price_fields.py
```

4. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 访问入口

- 后台管理：[http://localhost:8000/admin](http://localhost:8000/admin)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)
- 健康检查：[http://localhost:8000/health](http://localhost:8000/health)

## 微信接入

微信公众号或企业微信需要提供以下配置：

- `wechat_app_id`
- `wechat_app_secret`
- `wechat_token`
- `wechat_encoding_aes_key`

可以通过后台配置页写入：

- `/admin/api-settings`

Webhook 地址：

```text
GET  /wechat/webhook
POST /wechat/webhook
```

## OTA 接入

在后台配置：

- `ota_api_base`
- `ota_api_key`

联调时建议先使用 dry-run：

```bash
curl -X POST http://localhost:8000/api/external/ota-dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_id": 1,
    "competitor_id": 1,
    "target_date": "2026-04-26",
    "provider": "third_party"
  }'
```

## 发布

生成交付压缩包：

```bash
python scripts/build_release.py
```

发布包默认排除以下内容：

- 本地数据库文件
- `.env`
- `tests/`
- 日志、缓存、`__pycache__`
- Git 与 IDE 元数据
- 本地调试与模拟脚本
