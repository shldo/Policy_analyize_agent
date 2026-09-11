# Policy Research Agent Demo Runbook

本说明用于本地、隔离环境的可复现 Demo。它不是生产部署手册，也不授权修改冻结评测库。

## 运行前提

需要：

- Windows + Docker Desktop；
- 项目依赖已安装，后端 Python 环境和前端 Node/npm 可用；
- 运行时模型的 API 配置或本地模型资源；
- 需要演示的冻结 PDF/Child/Parent 数据已在目标隔离环境准备好；
- 一个临时普通账号。不要复制或提交 `private-test-user.json`、浏览器状态文件或任何 secret。

当前代码默认 `reranker_top_k + original`。P2 `per_document_backfill_v1` 仍是显式实验开关，不是默认 Demo 行为。

## 数据库隔离与迁移

不要对已有 `policy-parent-child-db` 或正式/评测快照执行迁移、初始化、测试写入或账号创建。

推荐使用新的 Compose project 和新的端口，避免复用旧 volume：

```powershell
$env:COMPOSE_PROJECT_NAME = "policy-closeout-demo"
$env:DB_PORT = "55432"
$env:WEB_PORT = "5300"
$env:APP_ENV_FILE = ".env.production"
docker compose up --build
```

首次创建新 volume 时，Compose 会按 `init.sql` 和 `database/migrations/` 的顺序建立 schema，其中包含 migration 020。已有数据库必须由维护者按正式迁移流程单独应用 020；本后端启动时会只读检查 `generation_allowed`、`coverage_status`、`answer_status`，缺列会明确报错并停止，不能靠刷新绕过。

`.env.production` 只放在本地受保护位置，配置变量名称包括：

- `APP_SECRET`
- `ADMIN_REGISTER_SECRET`
- `DATABASE_URL` / `DATABASE_ENABLED`
- 运行时模型 provider、model 和 API key 配置
- `RAG_PACKING_POLICY`（默认 `original`）

文档、日志和截图中不得出现这些变量的值。

## 启动与健康检查

启动后访问：

- Web：`http://127.0.0.1:5300`
- API health：`http://127.0.0.1:5300/api/v1/health`

如果只做前端开发预览，可在 `frontend` 目录运行 `npm run dev`，但真实聊天验收必须指向隔离后端，不要把开发前端连到冻结评测库。

## Demo 场景

### 1. 登录与政策库

使用普通账号登录，确认政策库显示预期的 5 份文档及普通用户权限。普通用户不应看到或调用 admin 设置、导入和管理接口。

### 2. Direct 单文档

在 Document Analysis 中只选择一份文档，提问：

> What does the provided policy material say about responsible AI staff training? Cite the source and state any evidence gaps.

预期：回答紧邻 Child 引用，保留主体、条件和期限；如果覆盖未确认，显示 `Evidence coverage not confirmed` 类提示，而不是把未知写成 complete，也不要把部分证据直接改成 withheld。

### 3. 多文档与 Agent

选择有权限的多份文档，切换 Agent (ReAct)，使用一个需要跨文档比较的问题。检查工具来源、最终引用和最终 packed Child 一致；只在 Open Discussion 中演示 full-corpus。Document Analysis 不应因为测试问题而偷偷启用 full-corpus 工具。

### 4. 部分回答

使用一个已知只能覆盖部分证据的问题。预期：系统回答已有依据的部分，并明确 `provided material` 的缺口；不显示完整覆盖，不把“未找到”改写成“全文不存在”。

### 5. 多轮、刷新与引用抽屉

发送 follow-up，刷新页面并重新打开历史消息。确认当前消息的 coverage/answer 状态独立保存，旧消息缺少状态时显示 unknown/not assessed；打开 citation drawer，检查 Child 原文和页码，点击 PDF 后确认页码，而不是只检查按钮存在。

### 6. 网络故障

在隔离环境中人工中断 API 请求或断开本地后端，确认 UI 显示：

> Connection interrupted. Please retry.

不会自动重发、不会出现伪成功，历史消息不会从 streaming/error 变成 generated。不要把 provider 原始异常粘贴给用户。

## 状态解释

- `generation_allowed=true`：允许基于当前上下文生成，不等于完整支持。
- `coverage_status=complete`：只有经过明确完整验证且最终 Child 仍在 packed context 才可使用。
- `coverage_status=partial`：可以有依据地回答部分内容，但不是完整答案。
- `coverage_status=not_assessed`：当前没有足够的完整性证明；不是拒答理由。
- `coverage_status=no_context` + `answer_status=withheld`：没有可用上下文，系统拒绝生成文档答案。
- citation 编号合法只说明身份可追踪，不说明引用语义支持相邻断言。

## 回退与停止

将运行配置设为：

```text
RAG_PACKING_POLICY=original
```

重启 backend/worker 即可回退到原始 packing。selection 默认保持 `reranker_top_k`。回退不需要重建 embedding、不需要重新入库，也不应修改题库或数据库快照。

停止本轮 Demo：

```powershell
docker compose down
```

不要对不确定的项目运行 `docker compose down -v`，避免删除仍需复核的 volume。临时 Demo volume 的清理由维护者依据绝对路径和项目名单独确认。

## 常见问题

- **启动提示 migration 020 required**：目标库是旧 schema。停止服务，确认它不是冻结库，再按迁移流程应用 020；不要让代码自动修改库。
- **页面显示 Connection interrupted**：检查后端 health、隔离端口、API key 和模型服务状态；手工重试一次即可，不要自动循环。
- **回答带有 Evidence coverage not confirmed**：这是保守状态，不是前端故障；需要人工检查证据完整性。
- **引用编号存在但事实仍不确定**：编号校验不是语义支持校验，按 Child 原文逐断言复核。
- **模型/数据缺失**：本仓库不会凭空重建 ignored PDF、模型缓存或冻结数据库；补齐后记录版本和 hash，再执行 Demo。

## 最后一轮工程收尾记录（2026-09-11）

F1–F4 的确定性修复已进入当前工作区：Direct history finalize 接口、状态降级、显式 citation number 和旧编号兼容均有回归测试。离线审计已生成 50/50 个逐题记录，位置见 [FINAL_ENGINEERING_CLOSEOUT_20260911.md](FINAL_ENGINEERING_CLOSEOUT_20260911.md)。审计不会自动证明引用语义；`pending` 必须由人工按 Child 原文复核。

当前版本构建已验证，但 2026-09-11 的隔离 Compose 启动因 Docker Hub 拉取 `node:22-alpine` 网络超时而阻塞，尚未完成浏览器全路径；详见 [UI 验收记录](UI_ACCEPTANCE_20260911.md)。旧 UI 目录只能作为历史参考。首次 Demo 必须使用新隔离数据库并确认 migration 020 已应用，不能连接 `policy-parent-child-db`。

## 当前限制

本版本没有提高或重新计算检索覆盖；历史 C 基线仍为 Complete@20 `40/43`、Macro EGC@20 `95.03876%`。50 题 generation-only 已有 8 题 agent review、42 题 provisional evidence recheck，但没有人类签核，也没有全量独立质量分母。UN02/UN06 的语义引用风险、MC06/CS07 的覆盖缺口及当前版本浏览器验收仍是放行前事项。
