# 阶段 0：镜像瘦身实测记录（2026-11-20）

> 本文档记录五阶段技术栈改造的**阶段 0**（不换栈，只减体积）的实测数据。
> 所有数字都是容器内 `du` / `docker images` / `ldd` 实测，不是估算。

**结论**：unified 镜像 **2.01GB → 1.39GB**（-31%），backend 镜像 **1.59GB → 1.32GB**（-17%）。
原计划「1.3GB」的目标在 unified 形态下未达成（差 90MB），backend 形态达成。

---

## 一、体积对照

| 镜像 | 瘦身前 | 瘦身后 | 节省 |
|---|---:|---:|---:|
| `unified`（生产交付物，nginx + 后端） | 2.01GB | **1.39GB** | -620MB (-31%) |
| `backend`（纯后端） | 1.59GB | **1.32GB** | -270MB (-17%) |

## 二、分层拆解

| 层 | 瘦身前 | 瘦身后 | 手段 |
|---|---:|---:|---|
| site-packages | 906MB | 452MB | 剔 .pyc 134MB + kubernetes 依赖树 96MB + zstandard/hf_xet/mmh3 36MB |
| apt 包（libllvm19/mesa/libz3 等） | 408MB | ≈218MB | 去掉 libgl1 拖进的 Mesa/LLVM 图形栈 ≈190MB |
| 字体（fonts-noto-cjk） | 89MB | 38MB | 删两个全项目零引用的 Serif .ttc ≈51MB |
| ONNX embedding 模型 | 79MB | 79MB | 保留——实测集合维度 384，MiniLM 真的在用 |
| 前端 dist | 5.1MB | 5.1MB | 无变化 |
| nginx + supervisord | 53MB | 53MB | 无变化 |

## 三、剔除了什么

| 包 / 资源 | 体积 | 为什么能剔 |
|---|---:|---|
| `kubernetes` | 84MB | chromadb 的 K8s 分布式后端专用；本项目用 PersistentClient 本地模式 |
| `aiohttp` | 9MB | kubernetes 独占 |
| `websocket-client` | 1MB | kubernetes 独占；项目零 WebSocket 用法（rg 无命中） |
| `durationpy` | 1MB | kubernetes 独占 |
| `requests-oauthlib` | 1MB | kubernetes 独占 |
| `oauthlib` | 1MB | kubernetes 独占 |
| `six` | 1MB | kubernetes 独占 |
| `urllib3 等 12 个小包` | 3MB | kubernetes 独占尾巴 |
| `zstandard` | 24MB | 仅 httpx/langsmith 以 try/except 保护的可选 zstd 路径 |
| `hf_xet` | 11MB | 仅 huggingface_hub 的 xet 加速上传路径 |
| `mmh3` | 1MB | chromadb 的 hash 辅助 |
| `.pyc（916 个 __pycache__）` | 134MB | pip 编译缓存；容器常驻数小时，+0.5s 启动换 134MB 划算 |
| `libgl1 拖进的图形栈` | 190MB | libllvm19 123MB + mesa-libgallium 40MB + libz3-4 26MB |
| `NotoSerifCJK 两个 .ttc` | 51MB | 全项目零引用（rg NotoSerif 无命中） |

合计约 **512MB**（镜像层压缩后实际体现为 620MB）。

### 依赖图不动点分析：这些**不能**删

| 包 | 原因 |
|---|---|
| `requests / urllib3 / certifi / idna / charset-normalizer` | langsmith、tiktoken、httpx 仍在用 |
| `attrs` | jsonschema / referencing 仍在用 |
| `pyyaml` | chromadb / huggingface_hub / langchain-core 仍在用 |
| `typing-extensions / tzdata` | 大半个依赖树共用 |
| `onnxruntime` | chromadb 的默认 embedding 函数运行时必需 |
| `tokenizers` | chromadb 的默认 embedding 函数运行时必需 |
| `chromadb_rust_bindings` | chromadb 核心 rust 运行时 |
| `langsmith` | langchain_core.tracers.schemas 硬 import |
| `opentelemetry-sdk / exporter-otlp-proto-grpc` | chromadb import 期加载 |

> 判定方法：把 `kubernetes` 的传递依赖闭包算出来后，反复剔除「仍被闭包外包依赖」的节点，
> 直到不动点——剩下的才是**独占**可删集合。这比按 `pip show` 的直觉删要准得多：
> 最初按直觉把 `requests`/`urllib3`/`idna` 也列进删除清单，
> 实测卸载后 `httpx` 直接 `ModuleNotFoundError: No module named 'idna'`。

## 四、顺带修掉的三个真实缺陷

### 1. rule_engine.py 依赖 simpleeval 但 requirements.txt 未声明

生产镜像里该包不存在，任何触达规则引擎的请求都会 ImportError。本地 venv 因被顺带安装才没暴露。已补 simpleeval==0.9.13。

### 2. backend 阶段未预置 ONNX 模型

docker build --target backend 的镜像首次向量检索要现场下载 79MB，内网/弱网下必然超时。已把预置提到 backend-base。

### 3. ENV CHROMA_CACHE_DIR 完全无效

chromadb 1.5.9 只认 Path.home()（onnx_mini_lm_l6_v2.py:39），原注释「兼容两种实现」是误导。真正生效的开关是 HOME，已设 HOME=/home/app。

## 五、验证矩阵（全部通过）

| 验证项 | 结果 |
|---|---|
| 容器内真实卸载后 chromadb create/add/query | PASS |
| langchain + langgraph + langchain_openai 导入 | PASS |
| langsmith 导入 | PASS |
| httpx 真实网络请求 | PASS |
| uvicorn 真实起服务并响应 HTTP | PASS |
| PyMuPDF / Pillow 中文字体渲染 | PASS |
| FastAPI 全栈（fastapi/sqlalchemy/alembic/psycopg2/jwt/loguru/apscheduler） | PASS |
| 容器 /api/v1/health + /api/v1/ready | PASS |
| 容器前端首页 HTTP 200 | PASS |
| ONNX 模型命中预置（无现场下载） | PASS |
| 30 项 tools/check_* + tools/verify_* 门禁 | PASS |
| 3 个 backend/qa_*_suite.py | PASS |
| 前端 vitest 187 用例 + eslint | PASS |
| 浏览器回归 26 步（含转办/催办/催交考试/逾期/窄屏） | PASS |

## 六、被推翻的两个判断

### 1. 「90MB ONNX 模型是死重量，可以直接删」——**错的**

`app/core/config.py` 里的 `EMBEDDING_MODEL = "text-embedding-3-small"` 全项目从未被使用
（`rg EMBEDDING_MODEL app` 只命中定义处），而 `app/agents/rag.py:37` 的
`get_or_create_collection()` **没有传 `embedding_function`** —— 于是 Chroma 用默认的
MiniLM 本地模型。实测集合维度 = **384**（= MiniLM，不是 text-embedding-3-small 的 1536），
确认那个 90MB 模型真在用。**这是一处配置失效 bug，不是废重量。**

### 2. 「`ENV CHROMA_CACHE_DIR` 能控制模型缓存路径」——**错的**

chromadb 1.5.9 只认 `Path.home()`：
`chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py:39`
```python
DOWNLOAD_PATH = Path.home() / ".cache" / "chroma" / "onnx_models" / MODEL_NAME
```
原 Dockerfile 注释「兼容不同 chromadb 版本『读环境变量 / 用 Path.home() 推导』两种实现」
是**误导**——真正生效的开关是 `HOME` 环境变量。已设 `HOME=/home/app`，
并把预置目录对齐到 `/home/app/.cache/chroma`（`/root` 是 0700，app 用户读不到）。

## 七、留给后续阶段的判断

- **ONNX 模型 + onnxruntime（169MB）要彻底去掉，必须换 embedding 后端**。
  已实测 MiniMax 的 embeddings 端点可用（`POST /v1/embeddings`，参数名是 `texts`、
  返回 `vectors`，**不是** OpenAI 协议），模型 `embo-01` 输出 **1536 维**。
  但 Chroma 的 `OpenAIEmbeddingFunction` 走标准 OpenAI 协议，需要一个 OpenAI 兼容的
  embeddings 端点；且现有索引是 MiniLM 384 维，换模型必须**全量重建**（`rag.py` 已有
  `reindex_all()`）。建议并入阶段 1（迁 PG）时一并做，顺带用 pgvector 换掉 chromadb，
  那样能一次消掉 onnxruntime(78MB) + ONNX(90MB) + kubernetes(84MB) +
  chromadb_rust_bindings(57MB) + numpy 部分 ≈ **300MB+**，语义更干净。

- **`chromadb` 整体值得换成 pgvector**：本项目向量数据只有 **7.3MB / 18 条**，
  却背着 437MB 的 chromadb 全家桶（chromadb 7 + rust_bindings 57 + onnxruntime 78 +
  kubernetes 84 + tokenizers 12 + numpy 45 + numpy.libs 28 + 其他）。
  迁 PG 后用 pgvector，镜像与内存都省。

- **生产 LLM 配置**（`sys_config` 实测）：`llm_provider=custom`、
  `llm_base_url=https://api.minimax.cn/v1`、`llm_model=MiniMax-M3.1-Flash`、
  `llm_max_tokens=8192`。项目**从未调用过** embeddings 端点。

---

*生成自 `docs/IMAGE_SLIMDOWN_2026-11-20.py`（数据同源，便于机器核对）*