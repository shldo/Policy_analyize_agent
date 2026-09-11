# 当前版本 UI 验收记录

日期：2026-09-11

分支：`develop`
结论：`blocked / not passed`

本轮尝试创建新的 Compose project 和独立端口，未复用 `policy-parent-child-db`，也没有修改已有容器、volume 或冻结快照。新 project 在拉取 `node:22-alpine` 时因 Docker Hub 网络连接超时失败：

```text
failed to authorize ... auth.docker.io/token ... connectex ...
```

失败的临时 project 已清理；没有留下运行中的本轮容器。当前环境还缺少可直接用于浏览器验收的 Playwright 包和可演示的 PDF 数据文件，因此不能把静态构建或历史截图当作当前版本的浏览器通过证据。

## 已确认但不等于浏览器通过

- 前端 `npm run build` 已通过。
- 显式 citation number 的非连续解析、未知编号不可点击和旧无编号兼容已有自动化测试。
- Direct SSE 保存参数已有 autospec 回归测试。
- `complete + coverage_sufficient=false` 会降为 `not_assessed`，不能由历史读取升级为 complete。
- 未启动新隔离 API/前端，没有进行登录、Direct 保存、刷新、PDF 页码、Agent 全库模式或网络失败路径的真实浏览器操作。

## 仍需在环境恢复后执行的路径

1. 新隔离数据库应用 migration 020，启动 API/前端并创建临时普通账号。
2. Direct 生成后刷新历史，确认保存成功、状态不被升级。
3. 使用 `[1,3,7]` 与未知 `[2]` 引用，点击和刷新后仍定位正确 Child/PDF 页码。
4. Agent 在正确模式执行全库搜索；Document Analysis 不偷偷切换 full-corpus。
5. partial/not_assessed 不显示为 complete；无上下文才 withheld。
6. 中断网络请求，确认显示 `Connection interrupted. Please retry.`，不产生伪成功或自动重发。

恢复条件是 Docker 镜像可用、隔离 PDF/Child/Parent 数据可用、Playwright 或等价浏览器工具可用，以及运行时模型凭据已由维护者安全提供。完成后保留隔离环境至路径验收结束，再按项目名清理。
