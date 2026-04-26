# 基于 LangChain + Qwen3 + BGE-M3 的本地 RAG 系统

## Project Overview

本项目在 `finalProject/` 中实现一个**基于 Docker 组织形式的本地 RAG 系统**：

- 根目录负责容器编排与模型启动脚本
- `src/backend/` 负责后端 RAG 服务
- `src/frontend/` 负责前端页面与交互逻辑
- **Qwen3-4B** 通过 **vLLM 容器服务** 提供模型能力
- **BGE-M3** 作为 embedding 模型
- **LangChain** 作为整体设计思路参考，用于组织 RAG 链路

当前项目已经完成第一版骨架实现，目标是实现以下完整流程：

- 用户在前端输入问题
- 前端调用后端接口
- 后端完成文档加载、切分、检索与回答生成
- 后端通过 OpenAI-compatible API 调用本地 Qwen3
- 前端展示答案与检索来源

---

## 项目效果

当前项目已经实现一条可本地运行、可演示的 RAG 问答链路，具体效果如下：

- 前端使用 Vue 3 重构，支持状态检查、索引构建和问答提交
- 回答通过 SSE 逐 token 流式返回，页面可实时显示生成过程
- Think 内容与正式回答分离展示，默认可折叠查看
- 检索来源会以独立卡片展示，便于核对答案依据
- 支持本地知识库构建与重建，并可在 Docker Compose 中一键启动前后端与模型服务
- 已验证 BGE-M3 + FAISS 的可选检索链路，同时保留 simple vector store 作为轻量方案

如果浏览器看不到最新效果，通常是缓存或容器未重建完成，强制刷新即可。

---


## 整体架构

本项目采用**前后端分离 + 独立模型服务**的结构：

- **Frontend**：负责界面展示与用户交互
- **Backend**：负责 RAG 主链路
- **vLLM(Qwen3)**：负责最终回答生成
- **Vector DB**：负责本地检索索引

```mermaid
flowchart LR
    U[用户] --> F[Frontend]
    F --> B[Backend API]
    B --> D[Knowledge Base Documents]
    B --> S[Text Splitter]
    S --> V[Vector Store]
    B --> E[BGE-M3 Embedding]
    B --> L[vLLM / Qwen3-4B]
    V --> B
    B --> F
    F --> U
```

---

## Project Structure

```text
finalProject/
├── README.md                    # This document
├── docker-compose.yaml          # Container orchestration
├── start_vllm.sh                # Start local vLLM service for Qwen3
├── stop_vllm.sh                 # Stop local vLLM service
├── .env.example                 # Environment variable example
│
├── src/
│   ├── backend/                 # Backend RAG service
│   │   ├── app.py               # FastAPI application entry
│   │   ├── config.py            # Configuration management
│   │   ├── rag_chain.py         # RAG pipeline
│   │   ├── loader.py            # Document loading
│   │   ├── splitter.py          # Text splitting
│   │   ├── vector_store.py      # Local vector store
│   │   ├── embedding_client.py  # BGE-M3 wrapper (current simplified impl)
│   │   ├── llm_client.py        # Qwen3 client (OpenAI-compatible)
│   │   ├── prompt.py            # Prompt template
│   │   ├── requirements.txt     # Python dependencies
│   │   └── Dockerfile           # Backend container image
│   │
│   └── frontend/                # Frontend service
│       ├── index.html           # Main interface
│       ├── style.css            # Styles
│       ├── app.js               # Frontend logic
│       └── Dockerfile           # Frontend container image
│
├── data/
│   ├── raw/                     # Original knowledge base documents
│   └── processed/               # Optional processed files
│
├── vector_db/                   # Local vector database persistence
│
└── tests/                       # Test module
    ├── __init__.py
    ├── test_loader.py           # Document loading tests
    ├── test_splitter.py         # Splitting tests
    ├── test_retriever.py        # Retrieval tests
    ├── test_api.py              # API tests
    └── test_integration.py      # End-to-end tests
```

---

## 前端与后端职责划分

## Frontend

### Responsibilities

- 提供问题输入框
- 调用后端 API
- 展示模型回答
- 展示检索来源
- 展示索引构建和系统状态

### Tech Stack

- `HTML`
- `CSS`
- `Vue 3`
- `JavaScript`

### Port

- `9898`

### 当前页面功能

- 检查系统状态
- 构建索引
- 提交问题并以流式方式展示回答
- 展开 / 收起 Think 内容
- 展示回答与 sources

---

## Backend

### Responsibilities

- 提供 HTTP API
- 加载本地知识库文档
- 切分文本
- 生成 embedding
- 建立并读取本地向量索引
- 执行相似度检索
- 调用本地 Qwen3-4B 生成回答
- 将最终结果返回前端

### Tech Stack

- `FastAPI`
- `httpx`
- 本地向量检索实现
- OpenAI-compatible Qwen3 API

### Port

- `8001`

---

## Backend Module Design

### Module 1: Document Loader

**Responsibilities:**
- 读取 `data/raw/` 中的知识库文档
- 当前支持 `txt` 与 `md`
- 转换为统一的文档对象

---

### Module 2: Text Splitter

**Responsibilities:**
- 将长文档切分为多个 chunk
- 保留 overlap 以提升上下文连续性

**Current Parameters:**
- `chunk_size = 1200`
- `chunk_overlap = 150`

---

### Module 3: Embedding Layer

**Responsibilities:**
- 对文档块与用户问题做向量化
- 当前版本使用简化的本地 embedding 实现作为占位
- 后续可替换为真实 **BGE-M3** 模型推理

**说明：**
README 保留 BGE-M3 作为正式方案；当前代码中的 `embedding_client.py` 是一个可测试、可运行的轻量实现，便于先打通项目链路。

---

### Module 4: Vector Store

**Responsibilities:**
- 存储文档 embedding
- 提供持久化能力
- 支持相似度检索

**Current Implementation:**
- 本地 JSON 持久化的 simple vector store
- 可选 FAISS 向量库后端
- 余弦相似度检索

**Future Options:**
- `Chroma`
- 继续扩展更多向量库后端

---

### Module 5: LLM Integration

**Responsibilities:**
- 通过 OpenAI-compatible API 调用本地 Qwen3-4B
- 基于检索结果生成最终回答

**Connection Strategy:**
- 参考 `Lab3` 的服务定义，将 Qwen3 作为独立的 `vllm` 容器运行
- 镜像：`ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin`
- 端口：`8000`
- 服务角色：`Qwen3-4B language model`
- 后端访问地址：
  - 容器内：`http://vllm:8000/v1`
  - 宿主机调试：`http://localhost:8000/v1`

**Prompt Design:**

```text
你是一个基于本地知识库进行问答的助手。
请严格依据提供的上下文回答用户问题。
如果上下文中没有足够信息，请明确说明“我无法从当前知识库中找到足够依据”。
不要编造事实。

上下文：
{context}

问题：
{question}
```

---

## API Specification

### `GET /`

后端根路径，返回服务状态说明。

### `GET /api/health`

健康检查。

```json
{"status": "ok"}
```

### `GET /api/status`

检查后端、索引和模型服务状态。

```json
{
  "backend": true,
  "index_ready": true,
  "qwen_ready": true,
  "embedding_ready": true
}
```

### `POST /api/index`

构建或重建知识库索引。

```json
{
  "status": "ok",
  "message": "Index built successfully",
  "documents": 2,
  "chunks": 4,
  "index_ready": true
}
```

### `POST /api/chat`

用户提问并获取回答。当前默认返回流式 SSE 数据，前端会逐 token 展示答案。

```json
// Request
{"question": "什么是 RAG？"}
```

```json
// Response
{
  "answer": "RAG 是一种将检索与生成结合的问答方法。",
  "sources": [
    {
      "source": "intro.md",
      "content": "RAG combines retrieval and generation...",
      "score": 0.82
    }
  ]
}
```

### `POST /api/chat/stream`

用户提问并获取流式回答（SSE）。该接口作为 `/api/chat` 的兼容别名保留。

 - 返回类型：`text/event-stream`
 - 事件数据格式：
   - `{"type":"start"}`：流式开始
   - `{"type":"token","token":"..."}`：逐 token 输出
   - `{"type":"sources","sources":[...]}`：检索来源
   - `{"type":"done"}`：流式结束

前端当前实现为：提交问题后直接调用 `/api/chat`，并按 SSE 逐 token 渲染答案。

如果浏览器仍然命中旧版脚本，请强制刷新页面或清理缓存。当前前端已通过版本化脚本地址加载：`/app.js?v=20260419-uifix-2`。

当前流式链路已增加：

- SSE `start/token/sources/done` 事件序列
- 服务端 `no-cache` 与 `X-Accel-Buffering: no` 响应头，减少代理缓冲
- 前端将 think 内容与正式回答分离显示，默认可折叠查看

### `GET /ui`

返回前端页面文件（若存在）。

---

## Workflow

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend Service
    participant Backend as Backend RAG Service
    participant Retriever as Vector Retriever
    participant LLM as Qwen3-4B

    User->>Frontend: Input question
    Frontend->>Backend: POST /api/chat (SSE)
    Backend->>Retriever: Retrieve relevant chunks
    Retriever-->>Backend: Return context
    Backend->>LLM: Generate answer with context
    LLM-->>Backend: Stream tokens
    Backend-->>Frontend: Return answer stream + sources
    Frontend-->>User: Display final result and think panel
```

---

## Docker / Qwen3 Connection Configuration

Qwen3 的连接配置参考 `Lab3/README.md`：

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| LLM (vLLM) | `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin` | 8000 | Qwen3-4B language model |

也就是说，在本项目中，Qwen3 推荐继续作为一个独立的 `vllm` 服务运行，由后端通过 OpenAI-compatible API 访问。

### LLM Mode 切换

后端现在支持两种接法，前端和接口无需修改，只需要切换环境变量：

1. `local`：原本方式，连接本地 / 容器内的 vLLM
2. `api`：新增方式，连接外部 Qwen API 或任意 OpenAI-compatible API

推荐使用以下环境变量：

```env
LLM_MODE=local
QWEN_BASE_URL=http://vllm:8000/v1
QWEN_MODEL=/root/.cache/huggingface/Qwen3-4B-quantized.w4a16
QWEN_API_KEY=
QWEN_HEALTH_PATH=/models
```

如果你要接外部 API，可以改成：

```env
LLM_MODE=api
QWEN_BASE_URL=https://your-api-endpoint/v1
QWEN_MODEL=qwen-plus
QWEN_API_KEY=your_api_key
QWEN_HEALTH_PATH=/models
```

说明：

- `QWEN_BASE_URL` 需要指向 OpenAI-compatible 根路径，后端会自动请求：
  - `GET {QWEN_BASE_URL}{QWEN_HEALTH_PATH}`
  - `POST {QWEN_BASE_URL}/chat/completions`
- `QWEN_API_KEY` 非空时，会自动通过 `Authorization: Bearer ...` 发送
- `QWEN_HEALTH_PATH` 默认是 `/models`，如果你的 API 没有这个健康检查地址，可以按实际情况改掉

- `TOP_K`：最终返回给 LLM 的 chunk 数量
- `RETRIEVAL_FETCH_K`：初次向量检索候选数量（建议 >= TOP_K）
- `RETRIEVAL_STRATEGY`：`hybrid` / `vector`
  - `vector`：仅向量相似度
  - `hybrid`：向量分 + 词项重叠分融合重排
- `EXPAND_ADJACENT_CHUNKS`：是否补充相邻 chunk，提升上下文连续性

并且文档加载已支持：

- `.txt`
- `.md`
- `.pdf`（按页提取并清洗文本）

---

## Deployment

### 1. Start vLLM Service (Qwen3-4B)

可以使用根目录脚本启动：

```bash
cd finalProject
bash start_vllm.sh
curl -s http://localhost:8000/v1/models
```

停止：

```bash
bash stop_vllm.sh
```



---

### 2. Start Backend Service

```bash
cd finalProject/src/backend
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

---

### 3. Start Frontend Service

当前前端是一个静态页面，不需要 `npm install` 或前端框架开发服务器。进入前端目录后，使用 Python 启动一个静态文件服务即可：

```bash
cd finalProject/src/frontend
python -m http.server 9898
```

启动后，在浏览器访问：

```text
http://localhost:9898
```

如果前端页面已经启动，它会通过 `app.js` 调用后端接口，因此请确保后端已经运行在 `8001` 端口。

此外，如果不想单独启动静态服务，也可以直接访问后端提供的页面入口：

```text
http://localhost:8001/ui
```

---

### 4. 通过Docker Compose快速启动和停止

本项目推荐参考 `Lab3/docker-compose.yml` 的写法，把 **vllm + backend + frontend** 一起放入 compose 中统一管理。



启动（后台运行）：

```bash
cd finalProject
docker compose up --build -d
```

停止：

```bash
docker compose down
```

重新启动某个服务：

```bash
docker compose restart backend
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QWEN_BASE_URL` | `http://vllm:8000/v1` | Qwen3 API address inside docker compose |
| `QWEN_MODEL` | `/root/.cache/huggingface/Qwen3-4B-quantized.w4a16` | Model name |
| `EMBEDDING_MODEL_PATH` | `/opt/models/bge-m3` | Local BGE-M3 path |
| `EMBEDDING_BACKEND` | `simple` | Embedding backend: `simple` or `bge-m3` |
| `VECTOR_DB_DIR` | `./vector_db` | Vector DB directory |
| `VECTOR_BACKEND` | `simple` | Vector backend: `simple` or `faiss` |
| `DATA_DIR` | `./data/raw` | Knowledge base directory |
| `TOP_K` | `3` | Number of retrieved chunks |
| `BACKEND_HOST` | `0.0.0.0` | Backend host |
| `BACKEND_PORT` | `8001` | Backend service port |
| `FRONTEND_PORT` | `9898` | Frontend service port |
| `VLLM_IMAGE` | `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin` | vLLM container image |

可以参考 `.env.example`。

### Phase 2 Optional Dependencies

当前后端已支持后端切换脚手架：

- `EMBEDDING_BACKEND=bge-m3`：启用 `sentence-transformers` 的真实 embedding 路径
- `VECTOR_BACKEND=faiss`：启用 FAISS 向量检索路径

并已接入 LangChain Core 风格的 Prompt 组织层（`langchain_flow.py`）：

- 若已安装 `langchain-core`：使用 `ChatPromptTemplate` 组织系统提示词与用户问题
- 若未安装：自动回退到本地 native prompt 渲染

默认值仍为 `simple`，保持第一阶段兼容。

如需启用 Phase 2 真实实现，可额外安装：

```bash
cd finalProject/src/backend
pip install -r requirements.phase2.txt
```

---

## Testing

### Running Tests

建议在你的 `qwen3` conda 环境中运行测试。

```bash
cd finalProject
python -m pytest tests/ -v
```

### Current Test Files

| Test File | Focus |
|----------|-------|
| `test_loader.py` | 文档加载 |
| `test_splitter.py` | 文本切分 |
| `test_retriever.py` | 检索逻辑 |
| `test_api.py` | API 行为 |
| `test_integration.py` | 端到端问答流程 |

### Current Status

当前项目测试已通过第一版验证，适合作为课程项目基础版本继续增强。

---

## 当前实现说明

虽然 README 的设计目标是 **LangChain + Qwen3 + BGE-M3**，但当前代码为了先完成项目闭环，采用了以下策略：

- 保留 LangChain/BGE-M3/Qwen3 的整体架构设计
- 当前 `embedding_client.py` 是一个简化实现，用于先打通检索主链路
- 当前 `vector_store.py` 是轻量本地实现，用于先完成可测试的最小版本
- Qwen3 连接方式已经按照 vLLM/OpenAI-compatible API 的方式设计好

这意味着：

- **当前版本适合演示系统结构与最小可运行链路**
- **后续可以逐步把 embedding 和 vector store 替换为真实生产级组件**

---

## Recommended Next Steps

当前已完成Phase1和Phase2

### Phase 1
继续完成真实联调：
- 启动 vLLM
- 调用 `/api/index`
- 调用 `/api/chat`
- 验证和本地 Qwen3 连通

### Phase 2
将当前简化实现替换为：
- 真实 `BGE-M3` embedding
- 真实 `LangChain` 组织链路
- 真实 `Chroma` / `FAISS`
- 把 /api/chat 改成流式输出（已新增 `/api/chat/stream`）
- 前端支持 token-by-token 展示（已完成，含非流式回退）

### Phase 3
增强交互与可展示性：
- 更丰富的前端 UI
- 文档上传
- 多轮对话
- 检索来源高亮

---

## Summary

把 `finalProject` 改成 `Project/Gomoku/README.md` 那种 Docker 风格组织，**是可行的，而且已经完成了第一版实现**。

新的核心思路是：

- 根目录负责部署与编排
- `src/backend/` 负责 RAG 核心逻辑
- `src/frontend/` 负责问答界面
- Qwen3 按 Lab3 的方式通过 `vllm` 容器服务提供模型能力
- 后续如有需要，再决定是否把 embedding 服务继续拆分

完整链路可以概括为：

**Frontend → Backend API → Retriever / Vector DB → Qwen3 → Frontend**

---

## 快速开始（从环境配置到运行）

### 0）创建并激活 conda 环境

```bash
conda create -n rag python=3.10 -y
conda activate rag
```

### 1）安装后端依赖

```bash
cd ./src/backend
pip install -r requirements.txt
```

### 2A）本地 vLLM 启动（local 模式，SSH / Linux bash）

终端 A（backend）：

```bash
cd ./src/backend
export LLM_MODE="local"
export QWEN_BASE_URL="http://localhost:8000/v1"
export QWEN_MODEL="/root/.cache/huggingface/Qwen3-4B-quantized.w4a16"
export QWEN_API_KEY=""
export QWEN_HEALTH_PATH="/models"
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

终端 B（vLLM）：

```bash
cd .
bash ./start_vllm.sh
```

终端 C（frontend）：

```bash
cd ./src/frontend
python -m http.server 9898
```

浏览器访问：

```text
http://localhost:9898
```

### 2B）Qwen API 启动（api 模式，SSH / Linux bash）

终端 A（backend）：

```bash
cd ./src/backend
export LLM_MODE="api"
export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export QWEN_MODEL="qwen-plus"
export QWEN_API_KEY="<YOUR_QWEN_API_KEY>"
export QWEN_HEALTH_PATH="/models"
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

终端 B（frontend）：

```bash
cd ./src/frontend
python -m http.server 9898
```

浏览器访问：

```text
http://localhost:9898
```

### 3）首次使用步骤

1. 点击 `检查系统状态`
2. 点击 `构建索引`
3. 在 `Ask` 区域输入问题并提交

---

## 已新增功能与作用说明

### A）API 接入增强（保留本地 vLLM）

- 新增可切换 LLM 模式：`local` / `api`
- 新增基于 API Key 的 OpenAI-compatible 调用路径
- 新增状态字段展示当前 LLM 的模式 / 地址 / 模型

**作用：** 使用同一套前后端即可灵活切换本地模型服务与云端 API。

### B）三个可见可用功能

1. **Top-K 检索滑块**
   - 可控制最终传给模型的检索片段数量。
   - **作用：** 可按问题类型在“精准”与“覆盖”之间调节。

2. **知识库文档浏览 / 预览**
   - 前端可直接查看已加载文档与内容预览。
   - **作用：** 提升可解释性，方便核对回答依据。

3. **最近问答历史面板**
   - 保存最近问答、来源、Top-K 等信息。
   - **作用：** 便于结果对比、复用与演示。

### C）RAG 实际质量增强

1. **PDF 文档处理**
   - 支持 `.pdf`（按页提取 + 文本清洗）。
   - **作用：** 扩展知识库来源，适配真实资料场景。

2. **句子边界感知切分**
   - 切分时优先按句子/换行边界并保留 overlap。
   - **作用：** 降低语义截断，提升检索与生成质量。

3. **Hybrid 重排 + 相邻 Chunk 扩展**
   - 先取候选（`RETRIEVAL_FETCH_K`），再融合向量分与词项重叠分重排。
   - 可选补充同文档相邻 chunk，增强上下文连续性。
   - **作用：** 提高相关性与答案完整度。

---

## 外部代码项目分析与上传（最新）

### 目录约定

外部代码项目统一放在：

```text
./data/code_projects/<project_name>/
```

例如：

```text
./data/code_projects/my_web_app/
./data/code_projects/my_backend_service/
```

并在 `.env` 中确保：

```env
CODE_PROJECTS_DIR=./data/code_projects
```

### 前端使用方式

1. 在页面中选择语料模式：`分析外部代码项目`
2. 选择已有外部项目，或直接上传 zip
3. 点击 `构建索引`
4. 提问（例如：项目核心模块、后端接口、调用流程）

### ZIP 上传接口（后端）

接口：`POST /api/code/upload`

- 请求类型：`multipart/form-data`
- 字段：
  - `project_name`：目标项目名
  - `file`：zip 文件

处理逻辑：

- 自动解压到 `CODE_PROJECTS_DIR/project_name`
- 自动进行安全路径校验（过滤非法路径）
- 解压完成后自动构建该外部项目索引

返回结果包含：

- `project_name`
- `documents`
- `chunks`
- `corpus` / `code_project`

### 与旧模式的差异

当前代码分析已聚焦到 **外部项目分析**，移除了“分析本项目代码”入口，避免模式混淆，流程更清晰：

- 知识库问答：`knowledge`
- 外部代码问答：`external_code`








