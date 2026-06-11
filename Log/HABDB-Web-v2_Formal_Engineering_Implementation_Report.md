# HABDB-Web-v2 正式工程实现报告

**生成时间：** 2026-06-11 15:23:05  
**项目路径：** `I:\论文\赤潮\文章\数据库文章\openclaw\codex\NAR\WebSite\HABDB-Web-v2`  
**目标：** 在 v1 原型基础上构建可运行、可部署、可维护、尽量达到 NAR 正式投稿版要求的正式数据库网站工程。  

## 1. 核心结论

HABDB-Web-v2 已被构建为标准工程化项目，而不是临时 MVP。当前版本包含：

- FastAPI 后端服务；
- PostgreSQL 数据库 schema；
- Redis + RQ 异步任务队列；
- DIAMOND 真实检索任务路径，优先使用既有 `HABs_Func_db.dmnd`；
- BLASTN / Kraken2 的 18SrRNA job workflow、配置项与索引挂载路径；
- React + Vite 前端，视觉风格保持 v1 的科研数据库风格；
- Docker Compose 管理 db、redis、backend、worker、frontend；
- 显式数据导入命令，不在普通 `docker compose up` 时反复扫描大型资源；
- `Resource_Preparation_Checklist.md` 记录索引准备状态；
- 全站用户可见命名统一为 `18SrRNA`。

## 2. 工程目录

```text
HABDB-Web-v2/
  backend/
    app/
      main.py
      models.py
      config.py
      database.py
      tasks/sequence_search.py
  frontend/
    src/App.jsx
    src/styles.css
  scripts/
    import_data.py
    build_indexes.py
    verify_release.py
  docker/postgres/init.sql
  docs/Resource_Preparation_Checklist.md
  docker-compose.yml
  Makefile
  .env.example
```

## 3. 命令设计

| 命令 | 作用 |
|---|---|
| `docker compose up -d` | 快速启动已有数据库和服务，不触发全量资源扫描。 |
| `make import-data` | 显式从 `/dataresource` 导入 HABDB 资源到 PostgreSQL。 |
| `make reset-db` | 清空并重建数据库后重新导入。 |
| `make bootstrap` | 新环境一键启动 db/redis、构建后端、导入数据、启动服务。 |
| `make build-indexes` | 检查 DIAMOND、构建/检查 BLASTN 18SrRNA、提示 Kraken2 索引准备。 |
| `make verify-release` | 检查 API、关键文件、manifest 与 18SrRNA 命名。 |

## 4. 数据库设计

v2 中已实现核心表：

- `species`
- `marker_sequence`
- `genome`
- `gene_family`
- `functional_sequence`
- `download_file`
- `statistic`
- `release_manifest`
- `search_job`

这些表覆盖 NAR 数据库网站需要的主要实体：物种、taxonomy 字段、18SrRNA marker、genome、CDS summary、功能基因、下载文件、统计缓存、发布 manifest 和序列检索任务。

## 5. 数据导入策略

导入脚本为：

```text
scripts/import_data.py
```

导入原则：

- 不复制 v1 的 33GB `dataresource`；
- 通过 Docker volume 将 `../HABDB-Web/dataresource` 只读挂载为 `/dataresource`；
- 用 `--reset` 显式清空重建；
- 默认检测已有数据，避免重复导入；
- 使用 stable HABDB IDs；
- 计算下载文件 checksum；
- 生成 statistics cache；
- 生成 release manifest；
- 将 `Toxic` 归一为 `toxic`、`harmful non-toxic`、`unknown`；
- 用户可见 marker label 统一为 `18SrRNA`。

## 6. 序列检索实现状态

| 模块 | 当前状态 |
|---|---|
| DIAMOND functional gene search | 已真实接入 worker，使用 `/dataresource/HABs_Func_db.dmnd`。 |
| BLASTN 18SrRNA search | API、job、worker 流程已实现；索引路径为 `/indexes/18SrRNA/habdb_18SrRNA`。 |
| Kraken2 18SrRNA classification | API、job、worker 流程已实现；索引路径为 `/indexes/kraken2_18SrRNA`。 |

DIAMOND 是第一优先真实运行路径。BLASTN 与 Kraken2 当前不使用假数据；若索引缺失，job 会返回 `waiting_for_index`，并提示具体缺失路径。

## 7. 18SrRNA 命名统一策略

v2 中，面向用户和未来报告统一使用 `18SrRNA`：

- 前端标题、统计卡、Graphical Abstract、搜索框、Tools 模块使用 `18SrRNA`；
- API summary 返回 `marker_label = 18SrRNA`；
- 数据库字段命名采用 `representative_18srrna`、`extended_18srrna_count`；
- 文档与清单使用 `18SrRNA`。

保留原始资源文件名中的历史 `18S` 字符串，例如 `HABs_18S_sequences.fasta`，因为这是既有文件路径，不应为了展示命名而破坏资源引用。

## 8. 验证状态

已完成静态验证：

- Python 文件语法检查通过；
- v2 工程目录与核心文件已生成；
- 前端文件已生成；
- 用户可见文档和 UI 采用 `18SrRNA` 命名；
- Docker Compose、Makefile、Resource Checklist 已生成。

未在当前会话中实际执行 Docker build，因为该步骤可能需要联网拉取镜像与 apt/npm 依赖。正式验证建议在可联网 Docker 环境中执行：

```powershell
cd "I:\论文\赤潮\文章\数据库文章\openclaw\codex\NAR\WebSite\HABDB-Web-v2"
copy .env.example .env
make bootstrap
make verify-release
```

## 9. 下一步建议

1. 在 Docker 环境中执行 `make bootstrap`。
2. 若 DIAMOND 容器包安装失败，改为固定使用包含 DIAMOND/BLAST/Kraken2 的 bioinformatics base image。
3. 对 `gene_family` 进一步建立人工词表，避免 accession-like 名称过细。
4. 增加 Alembic migration，替代当前 `metadata.create_all`。
5. 增加正式 Citation、Help、Version、Contact 页面。
6. 在公网部署前增加 HTTPS、Nginx、大文件下载代理、备份和监控。
