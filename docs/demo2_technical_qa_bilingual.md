# Demo 2 技术问答中英对照笔记

这份文档用于 Demo 2 前快速复习。建议回答 tutor 问题时始终围绕这条主线：前端界面接收用户操作，调用 `/api/v1` 后端接口，FastAPI router 把请求交给 service / repository，数据来自 PostgreSQL、pgvector 和文件系统，RAG 流程完成检索、rerank、evidence check，最后 LLM 生成答案并由前端展示 citations、sources 和 history。

This document is for quick revision before Demo 2. When answering tutor questions, keep returning to this flow: the frontend receives user actions, calls `/api/v1` backend APIs, FastAPI routers delegate work to services and repositories, data comes from PostgreSQL, pgvector, and the file system, the RAG pipeline performs retrieval, reranking, and evidence checking, and the LLM generates an answer that the frontend displays with citations, sources, and chat history.

## 1. 系统整体架构

我们的系统是一个面向政策学习和政策研究的 RAG workspace。前端使用 React、Vite 和 Material UI 构建 Chat、Library、Sources、Recent Chats、Document Drawer 和 metadata editing 等交互界面。后端使用 FastAPI 提供 REST API，负责用户认证、文档管理、PDF 处理、chunking、embedding、retrieval、reranking、evidence checking、chat history 和 LLM generation。数据库使用 PostgreSQL 保存用户、文档、metadata、pages、chunks、chat sessions 和 messages；同时用 pgvector 保存和检索 chunk embeddings。PDF 文件本体不直接存在数据库里，而是存在后端文件系统，例如 `backend/data/pdfs`。

Our system is a RAG workspace for policy learning and policy research. The frontend is built with React, Vite, and Material UI, and it provides the Chat page, Document Library, Sources panel, Recent Chats, Document Drawer, and metadata editing UI. The backend is built with FastAPI and provides REST APIs for authentication, document management, PDF processing, chunking, embedding, retrieval, reranking, evidence checking, chat history, and LLM generation. PostgreSQL stores users, documents, metadata, pages, chunks, chat sessions, and messages, while pgvector stores and retrieves chunk embeddings. The raw PDF files are not stored directly inside PostgreSQL; they are stored on the backend file system, for example under `backend/data/pdfs`.

## 2. 前端架构

前端的核心思想是把页面交互和 API 调用分开。`App.jsx` 管理全局状态，例如当前登录用户、documents 列表、以及已经加入 Chat 的 `contextSourceIds`。`api.js` 统一封装所有后端请求，并且所有请求都走 `/api/v1` 前缀。`ChatPage.jsx` 负责问答、sources、recent chats、citation drawer 和 document drawer；`LibraryPage.jsx` 负责文档搜索、筛选、分页、Add to chat、metadata edit；`DocumentDrawer.jsx` 被 Chat 和 Library 复用，用来显示文档 metadata 和 chunks。

The frontend separates UI interaction from API communication. `App.jsx` manages global state such as the current user, document list, and `contextSourceIds` selected for chat. `api.js` centralizes backend requests, and all backend requests go through the `/api/v1` prefix. `ChatPage.jsx` handles question answering, sources, recent chats, the citation drawer, and the document drawer. `LibraryPage.jsx` handles document search, filters, pagination, adding documents to chat, and metadata editing. `DocumentDrawer.jsx` is reused by both Chat and Library to display document metadata and chunks.

## 3. 前端向后端传了哪些关键参数

Chat 请求的核心参数包括 `question`、`document_ids`、`response_mode`、`answer_mode`、`session_id` 和 `history`。`question` 是用户输入的问题；`document_ids` 是用户选择的 source documents；`response_mode` 控制回答风格，可以是 `researcher` 或 `student`；`answer_mode` 控制知识边界，可以是 `analysis` 或 `chat`；`session_id` 用于继续已有历史会话；`history` 是为了兼容没有 session 的旧逻辑，最多传最近 5 轮对话。

The key Chat request parameters are `question`, `document_ids`, `response_mode`, `answer_mode`, `session_id`, and `history`. `question` is the user’s input. `document_ids` are the selected source documents. `response_mode` controls the writing style and can be `researcher` or `student`. `answer_mode` controls the knowledge boundary and can be `analysis` or `chat`. `session_id` is used to continue an existing chat session. `history` is kept for backward compatibility when there is no session, and it only sends the most recent 5 turns.

## 4. 后端架构

后端按业务模块组织。`auth` 模块负责登录、注册、token 和角色权限；`documents` 模块负责 PDF 上传、文本提取、metadata、chunking、embedding 和文档搜索；`chat` 模块负责 RAG 问答、chat sessions 和 messages；`settings` 模块负责 LLM API key 和 model 配置；`chat/rag` 模块负责 RAG workflow、prompt、evidence check 和 LLM generation。FastAPI router 只负责接收请求和返回响应，复杂业务逻辑放在 service 和 repository 中。

The backend is organized by business modules. The `auth` module handles login, registration, tokens, and role permissions. The `documents` module handles PDF upload, text extraction, metadata, chunking, embeddings, and document search. The `chat` module handles RAG-based Q&A, chat sessions, and messages. The `settings` module stores LLM API key and model configuration. The `chat/rag` module contains the RAG workflow, prompts, evidence checking, and LLM generation. FastAPI routers mainly receive requests and return responses, while complex logic is placed in services and repositories.

## 5. 数据库架构

数据库主要保存结构化数据。`app_users` 保存用户和角色；`documents` 保存文档基本信息、文件路径和处理状态；`document_metadata` 保存 title、summary、country、year、policy areas、keywords 等信息；`document_pages` 保存每页 PDF 文本；`document_chunks` 保存切分后的文本块；`chunk_embeddings` 保存每个 chunk 的向量；`processing_jobs` 保存文档处理任务状态；`chat_sessions` 保存聊天会话；`chat_messages` 保存用户和 AI 的消息、citations 和 evidence 状态。pgvector 的作用是让 PostgreSQL 可以存储向量并进行 similarity search。

The database stores structured data. `app_users` stores users and roles. `documents` stores basic document information, file paths, and processing status. `document_metadata` stores fields such as title, summary, country, year, policy areas, and keywords. `document_pages` stores extracted PDF page text. `document_chunks` stores the split text chunks. `chunk_embeddings` stores vectors for each chunk. `processing_jobs` stores document processing jobs. `chat_sessions` stores chat sessions. `chat_messages` stores user and assistant messages, citations, and evidence status. pgvector allows PostgreSQL to store vectors and run similarity search.

## 6. PDF 文档处理流程

PDF 处理流程从 Admin 上传文档开始。后端先保存 PDF 文件，然后用 PDF extractor 提取每页文本，把 pages 存入数据库。接着系统生成或保存 metadata，例如 title、summary、source、region、language、year、policy areas 和 keywords。然后 chunker 把 pages 切成带 overlap 的 chunks，再用 embedding model 把 chunk text 转成 384 维向量，最后把 chunks 和 embeddings 写入数据库。当整个流程完成后，文档状态从 uploaded / parsed / annotated 变成 ready。

The PDF processing pipeline starts when an admin uploads a document. The backend first saves the PDF file, then uses a PDF extractor to extract text page by page and stores the pages in the database. The system then generates or stores metadata such as title, summary, source, region, language, year, policy areas, and keywords. After that, the chunker splits pages into overlapping chunks, the embedding model converts chunk text into 384-dimensional vectors, and the chunks and embeddings are stored in the database. When the pipeline finishes, the document status moves from uploaded / parsed / annotated to ready.

## 7. Chunking 和 embedding 的关键优化

Sprint 2 里一个重要修复是 chunk size 和 embedding model tokenizer 对齐。之前 chunking 使用 `tiktoken` 估算 token 数，但 embedding model 自己有 tokenizer 和大约 512-token 限制，导致某些 chunk 在 embedding 时被静默截断，最终向量只代表残缺文本。现在系统使用 embedding model 自己的 tokenizer 计算 chunk 长度，并且对超长自然段做二次拆分。关键参数是 `MAX_CHUNK_TOKENS = 480` 和 `CHUNK_OVERLAP_TOKENS = 120`，这样既避免超限，又保留相邻 chunk 的上下文连续性。

An important Sprint 2 fix is aligning chunk size with the embedding model’s tokenizer. Previously, chunking used `tiktoken` to estimate token count, but the embedding model has its own tokenizer and roughly a 512-token limit. Some chunks were silently truncated during embedding, so their vectors represented incomplete text. Now the system uses the embedding model’s tokenizer to count chunk length and adds fallback splitting for oversized natural paragraphs. The key parameters are `MAX_CHUNK_TOKENS = 480` and `CHUNK_OVERLAP_TOKENS = 120`, which help avoid model truncation while preserving context continuity between adjacent chunks.

## 8. Library 模块

Library 是 source management 模块，用户可以浏览文档、搜索文档、筛选 metadata、查看文档详情、把文档加入 Chat sources，也可以通过 Edit dialog 修改 metadata。前端通过 `LibraryPage.jsx` 调用后端 documents API，例如 `GET /documents`、`GET /documents/search`、`GET /documents/{id}`、`GET /documents/{id}/chunks` 和 `PATCH /admin/documents/{id}`。Library 的意义是让用户先选择可信政策文档，再把它们作为 RAG 问答的检索范围。

The Library is the source management module. Users can browse documents, search documents, filter by metadata, inspect document details, add documents to Chat sources, and edit metadata through the Edit dialog. The frontend uses `LibraryPage.jsx` to call backend document APIs such as `GET /documents`, `GET /documents/search`, `GET /documents/{id}`, `GET /documents/{id}/chunks`, and `PATCH /admin/documents/{id}`. The Library allows users to select trusted policy documents first, and then use those documents as the retrieval scope for RAG-based Q&A.

## 9. Chat / RAG 问答流程

Chat 流程不是直接把问题发给 LLM。用户先选择 source documents，然后前端把 `question`、`document_ids`、`response_mode`、`answer_mode` 和 `session_id` 发给 `/api/v1/chat`。后端先做用户认证和 session 校验，再把问题 embed 成 query vector，从 selected documents 的 chunk embeddings 中检索 candidate chunks。系统不会只拿最终 top-k，而是先用 `candidate_limit = max(limit * 3, 20)` 拿更多候选，再交给 reranker 重新排序。之后 evidence check 判断证据是否足够，最后才调用 LLM 生成答案。

The Chat flow does not send the question directly to the LLM. The user first selects source documents, and the frontend sends `question`, `document_ids`, `response_mode`, `answer_mode`, and `session_id` to `/api/v1/chat`. The backend authenticates the user and validates the session, then embeds the question into a query vector and retrieves candidate chunks from the selected documents’ chunk embeddings. The system does not only retrieve the final top-k chunks; it first uses `candidate_limit = max(limit * 3, 20)` to fetch more candidates, then reranks them. After that, evidence checking decides whether the evidence is sufficient before the system calls the LLM to generate the final answer.

## 10. LangGraph RAG workflow

后端使用 LangGraph 把 RAG 流程拆成明确节点。workflow 的顺序是 `START -> load_documents -> retrieve_context -> check_evidence -> generate_answer 或 insufficient_evidence -> END`。`load_documents` 读取文档文本作为 fallback；`retrieve_context` 负责向量检索和 reranking；`check_evidence` 根据 context、raw chunks、pages 和 embedding 状态判断证据是否足够；如果证据足够就进入 `generate_answer`，否则在严格模式下进入 `insufficient_evidence`。

The backend uses LangGraph to split the RAG pipeline into clear nodes. The workflow order is `START -> load_documents -> retrieve_context -> check_evidence -> generate_answer or insufficient_evidence -> END`. `load_documents` reads document text as a fallback. `retrieve_context` handles vector retrieval and reranking. `check_evidence` evaluates whether the evidence is sufficient based on context, raw chunks, pages, and embedding status. If evidence is sufficient, the workflow goes to `generate_answer`; otherwise, in strict mode it goes to `insufficient_evidence`.

## 11. Reranker 和 evidence check

Reranker 是第二阶段相关性判断。第一阶段 pgvector similarity search 找到语义上相近的 candidate chunks，但相似不一定等于能回答问题，所以系统再用 cross-encoder reranker 计算问题和 chunk 的实际相关性。Evidence check 使用两个主要阈值：`MAX_VECTOR_DISTANCE = 0.45` 和 `MIN_RERANKER_SCORE = -7.0`。如果最近 chunk 的 vector distance 仍然太大，或者 reranker 最高分仍然太低，系统就认为 selected documents 中没有足够证据。

The reranker is a second-stage relevance check. The first-stage pgvector similarity search finds semantically similar candidate chunks, but similarity does not always mean the chunk actually answers the question. Therefore, the system uses a cross-encoder reranker to score the actual relevance between the question and each chunk. Evidence checking uses two main thresholds: `MAX_VECTOR_DISTANCE = 0.45` and `MIN_RERANKER_SCORE = -7.0`. If the closest chunk still has a high vector distance, or if the best reranker score is still too low, the system treats the selected documents as insufficient evidence.

## 12. Document Analysis 和 Open Discussion

系统用 `answer_mode` 控制知识边界。`analysis` 对应 Document Analysis，是严格模式，只允许基于 selected document excerpts 回答；如果 evidence 不足，就返回 insufficient evidence，不强行生成答案。`chat` 对应 Open Discussion，是开放讨论模式，可以结合模型的一般知识继续解释，但前端会显示 low-confidence warning，并要求区分文档证据和 general knowledge。简单说，`answer_mode` 控制“能不能用文档外知识”。

The system uses `answer_mode` to control the knowledge boundary. `analysis` corresponds to Document Analysis, which is strict and only allows answers grounded in selected document excerpts. If evidence is insufficient, it returns an insufficient evidence message instead of forcing an answer. `chat` corresponds to Open Discussion, which can use the model’s general knowledge for broader explanation, but the frontend shows a low-confidence warning and the answer should distinguish document evidence from general knowledge. In short, `answer_mode` controls whether the system can use knowledge beyond the selected documents.

## 13. Researcher 和 Student 模式

系统用 `response_mode` 控制回答风格。`researcher` 面向政策研究者或 practitioner，语言更专业、信息密度更高、可以使用政策术语；`student` 面向学习者，解释更清楚，尽量减少 jargon，并在必要时解释专业概念。可以记住一句话：`response_mode` 管“怎么说”，`answer_mode` 管“能基于什么说”。

The system uses `response_mode` to control writing style. `researcher` targets policy researchers or practitioners, using more professional language, higher information density, and policy terminology. `student` targets learners, using clearer explanations, less jargon, and brief definitions when technical terms are necessary. A useful sentence to remember is: `response_mode` controls “how to say it,” while `answer_mode` controls “what knowledge boundary the answer must follow.”

## 14. Chat history 和 session 管理

Chat history 由 `chat_sessions` 和 `chat_messages` 两张表实现。`chat_sessions` 保存 session title、user id、document ids、response mode、created time 和 updated time；`chat_messages` 保存 user 和 assistant 的消息、citations、evidence status 等。前端 Recent Chats 调用 `getChatSessions` 和 `getChatSession` 读取历史，恢复消息和 sources。系统设置 `MAX_HISTORY_TURNS = 5`，意思是最多把最近 5 轮历史传给 LLM，避免 prompt 太长和 token 成本过高。

Chat history is implemented using the `chat_sessions` and `chat_messages` tables. `chat_sessions` stores the session title, user id, document ids, response mode, created time, and updated time. `chat_messages` stores user and assistant messages, citations, evidence status, and related fields. The frontend Recent Chats panel calls `getChatSessions` and `getChatSession` to load history and restore messages and sources. The system uses `MAX_HISTORY_TURNS = 5`, meaning only the most recent 5 turns are sent to the LLM to avoid overly long prompts and high token cost.

## 15. Session ownership 安全校验

我这次修复的安全点是 session ownership check。因为 `session_id` 是前端传来的，后端不能默认相信它属于当前用户。现在 `/chat` 在继续已有 session 前，会先调用 repository 检查这个 session 是否属于当前 user。如果不属于，就返回 404，不会继续读取历史消息。这个改动不会影响正常用户继续自己的 session，但可以防止用户通过猜测或传入别人的 session id 来访问别人的 chat history。

The security fix I added is session ownership checking. Since `session_id` comes from the frontend, the backend cannot assume it belongs to the current user. Now `/chat` checks through the repository whether the session belongs to the current user before continuing it. If it does not belong to the user, the backend returns 404 and does not read the chat history. This does not affect normal users continuing their own sessions, but it prevents users from accessing another user’s chat history by guessing or passing a different session id.

## 16. Sprint 2 相比 Sprint 1 的主要提升

Sprint 2 的主要变化是从“基础文档问答”推进到“更完整的 policy research workflow”。Chat history 现在真正可用，Recent Chats 放在 Chat 左侧，可以恢复 messages 和 sources；Evidence check 更严格，结合 vector distance 和 reranker score；chunking 修复了 embedding tokenizer mismatch 和 silent truncation；Library 变成了可管理文档 metadata 的工具；Chat 页面 full-height，Sources、Recent Chats 和 answer panel 各自滚动，使用体验更接近真实产品。

The main Sprint 2 improvement is moving from basic document Q&A to a more complete policy research workflow. Chat history is now actually usable: Recent Chats are placed in the left side of the Chat page and can restore messages and sources. Evidence checking is stricter by combining vector distance and reranker score. Chunking fixes the embedding tokenizer mismatch and silent truncation issue. The Library has become a tool for managing document metadata. The Chat page is now full-height, and Sources, Recent Chats, and the answer panel scroll independently, making the system feel more like a real product.

## 17. 如果 tutor 问：为什么不用 LLM 直接回答？

中文回答：因为我们的目标是政策文档分析，而不是普通聊天。如果直接让 LLM 回答，它可能使用训练数据或编造内容。我们使用 RAG，让用户先选择 source documents，后端只从这些文档里检索 chunks，再把检索到的 context 和 citation instruction 传给 LLM。这样答案更可追溯，也更适合政策研究场景。

English answer: Because our goal is policy document analysis, not general chatting. If we let the LLM answer directly, it may rely on pretrained knowledge or hallucinate. We use RAG so that users first select source documents, the backend retrieves chunks only from those documents, and the retrieved context plus citation instructions are passed to the LLM. This makes the answer more traceable and more suitable for policy research.

## 18. 如果 tutor 问：为什么要 pgvector？

中文回答：我们既需要关系型数据，也需要向量检索。PostgreSQL 适合保存 users、documents、metadata、chat sessions 等结构化数据，pgvector 可以在同一个数据库里保存 chunk embeddings，并根据用户问题做 similarity search。这样不用额外维护一个独立 vector database，系统架构更简单。

English answer: We need both relational data and vector retrieval. PostgreSQL is suitable for storing structured data such as users, documents, metadata, and chat sessions, while pgvector allows us to store chunk embeddings and run similarity search inside the same database. This avoids maintaining a separate vector database and keeps the architecture simpler.

## 19. 如果 tutor 问：为什么要 reranker？

中文回答：向量检索适合找语义相近的候选文本，但相似文本不一定真的回答了问题。Reranker 是第二阶段过滤，用 cross-encoder 更精细地判断 question 和 chunk 的相关性。这样 evidence check 更可靠，最终给 LLM 的上下文也更准确。

English answer: Vector search is good at finding semantically similar candidate passages, but a similar passage may not actually answer the question. The reranker is a second-stage filter that uses a cross-encoder to judge the relevance between the question and each chunk more precisely. This makes evidence checking more reliable and improves the quality of the context passed to the LLM.

## 20. 如果 tutor 问：证据不足时系统怎么办？

中文回答：系统会根据 answer mode 决定行为。如果是 Document Analysis 模式，证据不足时会返回 insufficient evidence，不会强行回答。如果是 Open Discussion 模式，系统可以继续回答，但会显示 low-confidence warning，并说明 selected documents 提供的证据有限。这是为了平衡严谨分析和学习讨论。

English answer: The system behaves differently depending on the answer mode. In Document Analysis mode, if evidence is insufficient, it returns an insufficient evidence message and does not force an answer. In Open Discussion mode, it can still answer, but it shows a low-confidence warning and explains that the selected documents provide limited evidence. This balances strict analysis with exploratory learning.

## 21. 如果 tutor 问：Library metadata 编辑有什么意义？

中文回答：Metadata 不只是展示用的，它会影响用户搜索、筛选和理解文档。比如 policy areas、keywords、country、year 和 summary 可以帮助用户更快找到相关政策文件，也能帮助他们选择更合适的 sources 进入 Chat。Library Edit dialog 让 admin 能修正自动生成或不完整的 metadata，提高文档库质量。

English answer: Metadata is not only for display; it affects search, filtering, and document understanding. Fields such as policy areas, keywords, country, year, and summary help users find relevant policy documents faster and choose better sources for Chat. The Library Edit dialog allows admins to correct automatically generated or incomplete metadata, improving the quality of the document library.

## 22. 如果 tutor 问：你的这次 PR 做了什么？

中文回答：我这次做的是后端质量和安全修复。第一，我更新了 evidence tests，让测试匹配新的 `raw_chunks` 和 `has_embeddings` 参数，并新增 reranker score 的测试，确保二次 evidence 判断被覆盖。第二，我给 `/chat` 增加 session ownership check，用户继续已有 session 前，后端会确认这个 session 是否属于当前 user。如果不属于，就返回 404，避免读取别人的历史记录。

English answer: My PR is a backend quality and security fix. First, I updated the evidence tests to match the new `raw_chunks` and `has_embeddings` parameters, and added a reranker-score test to cover the second-stage evidence check. Second, I added session ownership validation to `/chat`. Before continuing an existing session, the backend checks whether the session belongs to the current user. If it does not, it returns 404 and avoids reading another user’s chat history.

## 23. 最后 30 秒总结

中文总结：我们系统是 React + FastAPI + PostgreSQL/pgvector 的政策文档 RAG workspace。前端负责 Chat、Library、Sources、History 和 metadata editing；后端负责认证、PDF processing、chunking、embedding、retrieval、reranking、evidence checking 和 LLM generation。Sprint 2 的重点是让系统从基础问答变成更完整的研究工作流：历史记录可以恢复，sources 可以管理，evidence 判断更严格，chunking 修复了 embedding tokenizer mismatch，Library 可以编辑 metadata。我的修复主要是更新 evidence tests，并给 chat session 加 ownership check，提升测试可靠性和用户数据安全。

English summary: Our system is a React + FastAPI + PostgreSQL/pgvector policy document RAG workspace. The frontend handles Chat, Library, Sources, History, and metadata editing. The backend handles authentication, PDF processing, chunking, embedding, retrieval, reranking, evidence checking, and LLM generation. Sprint 2 focuses on turning the system from basic Q&A into a more complete research workflow: chat history can be restored, sources can be managed, evidence checking is stricter, chunking fixes the embedding tokenizer mismatch, and Library metadata can be edited. My fix mainly updates evidence tests and adds chat session ownership checking to improve test reliability and user data security.
