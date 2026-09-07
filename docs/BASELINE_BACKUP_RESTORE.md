# 扩容前基线备份与隔离恢复记录

日期：2026-09-07。备份目录：`D:\AIWorkspace\Projects\policy-research-agent\backend\data\backups\baseline_20260907T201925`。

## 实际完成

- PostgreSQL custom-format 数据库导出，包含业务表数据。
- 复制 source_documents、pdfs、evaluation、settings.json 和实际 APP_ENV_FILE 指向的 .env.local。
- 备份目录被 Git 忽略；数据库、账号数据、密钥及原始 PDF 未推送 GitHub。
- 使用源库相同的本地镜像 ID，创建独立容器 `policy-restore-check-20260907t201925`，network=none、不映射端口。
- 恢复使用 pg_restore --exit-on-error --no-owner --no-privileges，成功结束。未覆盖源数据库。
- 比较源库与恢复库 public schema 的 **27 张表**，行数及排序后的行内容 MD5 全部一致。
- 用备份目录中的 PDF 和恢复库运行 v4 校验：**43 处源锚点、29 道可回答题映射、202 个片段及向量**通过。
- 恢复库语料快照与历史基线一致：`b7e675ee0c8846172070f1448e7d71046f0888b6c82f33affe1477ad62b57993`。
- 未加载生成模型、未调用 API、未重新观察检索排名。
- 验证后已停止并保留独立恢复容器；源项目服务保持运行。

## 本地验证文件

- `database.dump`：数据库备份。
- `restore_verification.json`：27 表内容比较以及当时 35 个备份文件的 SHA256。
- `restore_validation/benchmark_20260907T122212438014Z.json`：直接使用恢复库与备份 PDF 的评测校验。

SHA256 清单生成后又新增了恢复校验报告，故 35 文件清单不包含后续校验文件本身。表内容 MD5 用于一致性比较，不作为防恶意篡改的安全认证。

## 验证边界

这次证明业务数据与当前评测语料可以恢复，不是整套应用灾备演练。未逐项验证用户登录、数据库角色/权限、序列、模型缓存、TLS 或跨设备恢复；no-owner/no-privileges 也意味着未验证原角色授权恢复。

模型缓存未复制，依赖代码/模型配置恢复；实际云端模型服务的逐字输出不可保证。备份为同一磁盘的本地副本，未加密，不抵御磁盘损坏，不应公开分享。settings.json、.env.local 和数据库都可能包含敏感信息；本次不额外上传外部存储。

扩容时保留该目录，优先新建实验数据库。新备份使用新目录，禁止覆盖已有验证结果。若需要离机备份或共享，先决定加密和权限方案。

## 可复用校验入口

恢复到独立容器后，从 backend 运行：

```text
python -m evaluation.verify_restore --source <源容器> --restored <policy-restore-check-开头的恢复容器> --backup-dir <新备份目录>
```

该程序只读取两侧 public 表并写本地校验报告，不创建、删除或覆盖数据库。要求两个不同容器，输出文件已存在时拒绝覆盖。真实恢复命令应明确核对隔离目标后执行；不要将 pg_restore 指向现有业务库。
