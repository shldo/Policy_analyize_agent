# 本地 Docker 启动

在项目根目录执行，要求 Docker Desktop Linux 引擎和 Docker Compose 可用。

首次复制本地配置（已有文件时不要覆盖）：

```powershell
Copy-Item .env.local.example .env.local
docker compose --env-file .env.local up -d --build
docker compose --env-file .env.local ps
```

如果使用本机 Clash 且 Docker Hub 下载超时，可在当前 PowerShell 会话中设置已确认的代理端口，再执行构建：

```powershell
$env:HTTP_PROXY = 'http://127.0.0.1:7890'
$env:HTTPS_PROXY = 'http://127.0.0.1:7890'
docker compose --env-file .env.local up -d --build
```

7890 是本机实测端口，其他电脑需要使用自己的配置。此设置仅作用于当前 shell 及子进程，不修改系统代理；不要把容器内的 127.0.0.1 当作宿主机代理地址。

浏览器访问 http://localhost:8080，API 文档 http://localhost:8080/docs。
数据库供本机工具访问：127.0.0.1:55432，数据库 testdb，用户 appuser，密码见 .env.local。
本地配置包含公开的开发密码，只用于本机；云部署需另设密码、APP_SECRET、访问控制与 HTTPS。

配置使用独立 Compose 项目名 policy-research-agent-local。数据库保存在该项目的 pg_data 卷，上传文件和模型缓存保存在 backend/data。启动不会导入原项目数据库，也不会复制原 API 密钥。首次构建需要下载镜像和依赖；文档向量化还需要可用的模型或模型下载网络。

## 检查与停止

```powershell
docker compose --env-file .env.local logs --tail 80 db backend web
docker compose --env-file .env.local exec -T db psql -U appuser -d testdb -c "SELECT column_name FROM information_schema.columns WHERE table_name='chat_messages' AND column_name='token_usage';"
docker compose --env-file .env.local stop
```

不要使用 down -v 清除数据。备份数据库时还需保存上传文件，单独的数据库备份不包含 PDF 文件。

## 已有数据库补迁移 018

initdb.d 只在空数据卷初始化时执行。已有数据库先备份，再执行：

```powershell
docker compose --env-file .env.local exec -T db psql -v ON_ERROR_STOP=1 -U appuser -d testdb -f /docker-entrypoint-initdb.d/19_migration_018.sql
```

## 模型和验收

服务启动不等于模型问答通过。登录后按现有管理流程配置 LLM、Embedding、Reranker；模型密钥不提交到 Git。
随后验证文档上传、解析入库、检索、带引用问答、聊天历史和人工确认恢复。
真实模型评测、语料恢复和性能基线仍按 WORK_PLAN.md 单独执行。

部署用 Compose 默认端口目前只绑定本机。未来迁云时需明确 WEB_BIND_ADDRESS、域名与 TLS；不要直接开放数据库端口。
