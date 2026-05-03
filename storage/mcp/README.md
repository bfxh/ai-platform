# MCP Servers 资源收集

> Model Context Protocol (MCP) 服务器收集整理
> 更新时间：2026-03-24

## 📚 目录结构

```
\python\MCP\
├── README.md                    # 本文件
├── 📁 Official/                 # 官方MCP服务器
├── 📁 Filesystem/               # 文件系统相关
├── 📁 Database/                 # 数据库相关
├── 📁 Browser/                  # 浏览器/网络相关
├── 📁 Code-Execution/           # 代码执行相关
├── 📁 Git/                      # Git版本控制
├── 📁 Cloud/                    # 云服务相关
├── 📁 AI-ML/                    # AI/机器学习
├── 📁 Development/              # 开发工具
├── 📁 Utilities/                # 实用工具
├── 📁 Communication/            # 通讯工具
├── 📁 Search/                   # 搜索服务
├── 📁 Monitoring/               # 监控服务
├── 📁 Security/                 # 安全服务
├── 📁 Data-Science/             # 数据科学
├── 📁 Business/                 # 商业工具
├── 📁 Media/                    # 媒体处理
└── 📁 IoT/                      # 物联网
```

---

## 🏢 Official - 官方MCP服务器

| 名称 | 描述 | 链接 | 安装 |
|------|------|------|------|
| **filesystem** | 文件系统操作（读写、搜索） | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | `npx -y @modelcontextprotocol/server-filesystem` |
| **git** | Git仓库操作 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/git) | `npx -y @modelcontextprotocol/server-git` |
| **github** | GitHub API集成 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/github) | `npx -y @modelcontextprotocol/server-github` |
| **gitlab** | GitLab API集成 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/gitlab) | `npx -y @modelcontextprotocol/server-gitlab` |
| **postgres** | PostgreSQL数据库 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres) | `npx -y @modelcontextprotocol/server-postgres` |
| **sqlite** | SQLite数据库 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite) | `npx -y @modelcontextprotocol/server-sqlite` |
| **fetch** | HTTP请求获取 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | `npx -y @modelcontextprotocol/server-fetch` |
| **puppeteer** | 浏览器自动化 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer) | `npx -y @modelcontextprotocol/server-puppeteer` |
| **brave-search** | Brave搜索引擎 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search) | `npx -y @modelcontextprotocol/server-brave-search` |
| **sequential-thinking** | 顺序思考工具 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) | `npx -y @modelcontextprotocol/server-sequential-thinking` |
| **slack** | Slack集成 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/slack) | `npx -y @modelcontextprotocol/server-slack` |
| **memory** | 知识图谱记忆 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | `npx -y @modelcontextprotocol/server-memory` |
| **time** | 时间工具 | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/time) | `npx -y @modelcontextprotocol/server-time` |

---

## 📁 Filesystem - 文件系统

| 名称 | 描述 | 链接 |
|------|------|------|
| **filesystem** | 官方文件系统服务器 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **everything** | 访问整个文件系统 | [mcp-get](https://github.com/mcp-get/community-servers) |
| **obsidian** | Obsidian笔记集成 | [calclavia/mcp-obsidian](https://github.com/calclavia/mcp-obsidian) |
| **gdrive** | Google Drive集成 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **dropbox** | Dropbox集成 | [GitHub](https://github.com/jamsocket/mcp-dropbox) |
| **onedrive** | OneDrive集成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **s3** | AWS S3文件存储 | [GitHub](https://github.com/modelcontextprotocol/servers) |
| **box** | Box云存储 | [GitHub](https://github.com/box-community/mcp-server-box) |
| **nextcloud** | Nextcloud集成 | [GitHub](https://github.com/modelcontextprotocol/servers) |
| **ftp** | FTP服务器 | [GitHub](https://github.com/mcp-get/community-servers) |
| **sftp** | SFTP服务器 | [GitHub](https://github.com/mcp-get/community-servers) |
| **webdav** | WebDAV协议 | [GitHub](https://github.com/mcp-get/community-servers) |
| **rclone** | Rclone多云存储 | [GitHub](https://github.com/mcp-get/community-servers) |
| **syncthing** | Syncthing同步 | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🗄️ Database - 数据库

### SQL数据库

| 名称 | 描述 | 链接 |
|------|------|------|
| **postgres** | PostgreSQL官方 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **sqlite** | SQLite官方 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **mysql** | MySQL支持 | [designcomputer/mysql_mcp_server](https://github.com/designcomputer/mysql_mcp_server) |
| **mariadb** | MariaDB支持 | [GitHub](https://github.com/mcp-get/community-servers) |
| **mssql** | SQL Server | [GitHub](https://github.com/mcp-get/community-servers) |
| **oracle** | Oracle数据库 | [GitHub](https://github.com/mcp-get/community-servers) |
| **cockroachdb** | CockroachDB | [GitHub](https://github.com/mcp-get/community-servers) |
| **cockroachdb-serverless** | CockroachDB Serverless | [GitHub](https://github.com/mcp-get/community-servers) |
| **planetscale** | PlanetScale MySQL | [GitHub](https://github.com/mcp-get/community-servers) |
| **supabase** | Supabase PostgreSQL | [GitHub](https://github.com/mcp-get/community-servers) |

### NoSQL数据库

| 名称 | 描述 | 链接 |
|------|------|------|
| **mongodb** | MongoDB集成 | [kiliczsh/mcp-mongo-server](https://github.com/kiliczsh/mcp-mongo-server) |
| **redis** | Redis缓存 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **elasticsearch** | ES搜索 | [cr7258/elasticsearch-mcp-server](https://github.com/cr7258/elasticsearch-mcp-server) |
| **cassandra** | Apache Cassandra | [GitHub](https://github.com/mcp-get/community-servers) |
| **couchbase** | Couchbase | [GitHub](https://github.com/mcp-get/community-servers) |
| **dynamodb** | AWS DynamoDB | [GitHub](https://github.com/mcp-get/community-servers) |
| **firestore** | Google Firestore | [GitHub](https://github.com/mcp-get/community-servers) |
| **neo4j** | Neo4j图数据库 | [GitHub](https://github.com/mcp-get/community-servers) |
| **arangodb** | ArangoDB多模型 | [GitHub](https://github.com/mcp-get/community-servers) |
| **influxdb** | InfluxDB时序 | [GitHub](https://github.com/mcp-get/community-servers) |
| **timescaledb** | TimescaleDB时序 | [GitHub](https://github.com/mcp-get/community-servers) |
| **clickhouse** | ClickHouse分析 | [GitHub](https://github.com/mcp-get/community-servers) |

### 向量数据库

| 名称 | 描述 | 链接 |
|------|------|------|
| **chroma** | Chroma向量DB | [GitHub](https://github.com/mcp-get/community-servers) |
| **pinecone** | Pinecone托管 | [GitHub](https://github.com/mcp-get/community-servers) |
| **weaviate** | Weaviate开源 | [GitHub](https://github.com/mcp-get/community-servers) |
| **milvus** | Milvus分布式 | [GitHub](https://github.com/mcp-get/community-servers) |
| **qdrant** | Qdrant高性能 | [GitHub](https://github.com/mcp-get/community-servers) |
| **pgvector** | Postgres向量扩展 | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🌐 Browser - 浏览器/网络

| 名称 | 描述 | 链接 |
|------|------|------|
| **puppeteer** | 浏览器自动化 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **fetch** | HTTP请求 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **playwright** | 浏览器测试 | [executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright) |
| **browserbase** | 云端浏览器 | [browserbase/mcp-server-browserbase](https://github.com/browserbase/mcp-server-browserbase) |
| **selenium** | Selenium自动化 | [GitHub](https://github.com/mcp-get/community-servers) |
| **cypress** | Cypress测试 | [GitHub](https://github.com/mcp-get/community-servers) |
| **scrapingbee** | ScrapingBee爬虫 | [GitHub](https://github.com/mcp-get/community-servers) |
| **scrapy** | Scrapy爬虫框架 | [GitHub](https://github.com/mcp-get/community-servers) |
| **beautifulsoup** | BeautifulSoup解析 | [GitHub](https://github.com/mcp-get/community-servers) |
| **curl** | cURL请求 | [GitHub](https://github.com/mcp-get/community-servers) |
| **httpie** | HTTPie客户端 | [GitHub](https://github.com/mcp-get/community-servers) |
| **postman** | Postman集合 | [GitHub](https://github.com/mcp-get/community-servers) |
| **websocket** | WebSocket客户端 | [GitHub](https://github.com/mcp-get/community-servers) |
| **grpc** | gRPC客户端 | [GitHub](https://github.com/mcp-get/community-servers) |
| **graphql** | GraphQL客户端 | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 💻 Code-Execution - 代码执行

### 编程语言

| 名称 | 描述 | 链接 |
|------|------|------|
| **python** | Python执行 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **nodejs** | Node.js执行 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **deno** | Deno执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **bun** | Bun执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **typescript** | TypeScript执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **ruby** | Ruby执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **go** | Go执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **rust** | Rust执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **java** | Java执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **kotlin** | Kotlin执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **scala** | Scala执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **csharp** | C#执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **fsharp** | F#执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **php** | PHP执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **perl** | Perl执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **r** | R语言执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **julia** | Julia执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **lua** | Lua执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **swift** | Swift执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **dart** | Dart执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **elixir** | Elixir执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **clojure** | Clojure执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **haskell** | Haskell执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **ocaml** | OCaml执行 | [GitHub](https://github.com/mcp-get/community-servers) |
| **erlang** | Erlang执行 | [GitHub](https://github.com/mcp-get/community-servers) |

### 执行环境

| 名称 | 描述 | 链接 |
|------|------|------|
| **docker** | Docker容器 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **jupyter** | Jupyter Notebook | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **colab** | Google Colab | [GitHub](https://github.com/mcp-get/community-servers) |
| **kaggle** | Kaggle Kernels | [GitHub](https://github.com/mcp-get/community-servers) |
| **replit** | Replit环境 | [GitHub](https://github.com/mcp-get/community-servers) |
| **codesandbox** | CodeSandbox | [GitHub](https://github.com/mcp-get/community-servers) |
| **codepen** | CodePen | [GitHub](https://github.com/mcp-get/community-servers) |
| **stackblitz** | StackBlitz | [GitHub](https://github.com/mcp-get/community-servers) |
| **gitpod** | Gitpod环境 | [GitHub](https://github.com/mcp-get/community-servers) |
| **github-codespaces** | GitHub Codespaces | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🔀 Git - 版本控制

| 名称 | 描述 | 链接 |
|------|------|------|
| **git** | Git操作官方 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **github** | GitHub API | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **gitlab** | GitLab集成 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **bitbucket** | Bitbucket | [GitHub](https://github.com/mcp-get/community-servers) |
| **gitea** | Gitea集成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **gitee** | Gitee码云 | [GitHub](https://github.com/mcp-get/community-servers) |
| **azure-devops** | Azure DevOps | [GitHub](https://github.com/mcp-get/community-servers) |
| **sourcehut** | SourceHut | [GitHub](https://github.com/mcp-get/community-servers) |
| **codecommit** | AWS CodeCommit | [GitHub](https://github.com/mcp-get/community-servers) |
| **svn** | SVN版本控制 | [GitHub](https://github.com/mcp-get/community-servers) |
| **mercurial** | Mercurial | [GitHub](https://github.com/mcp-get/community-servers) |
| **perforce** | Perforce | [GitHub](https://github.com/mcp-get/community-servers) |

---

## ☁️ Cloud - 云服务

### 公有云

| 名称 | 描述 | 链接 |
|------|------|------|
| **aws** | AWS服务 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **gcp** | Google Cloud | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **azure** | Azure服务 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **alibaba-cloud** | 阿里云 | [GitHub](https://github.com/mcp-get/community-servers) |
| **tencent-cloud** | 腾讯云 | [GitHub](https://github.com/mcp-get/community-servers) |
| **huawei-cloud** | 华为云 | [GitHub](https://github.com/mcp-get/community-servers) |
| **oracle-cloud** | Oracle Cloud | [GitHub](https://github.com/mcp-get/community-servers) |
| **ibm-cloud** | IBM Cloud | [GitHub](https://github.com/mcp-get/community-servers) |
| **digitalocean** | DigitalOcean | [GitHub](https://github.com/mcp-get/community-servers) |
| **linode** | Linode | [GitHub](https://github.com/mcp-get/community-servers) |
| **vultr** | Vultr | [GitHub](https://github.com/mcp-get/community-servers) |
| **hetzner** | Hetzner | [GitHub](https://github.com/mcp-get/community-servers) |

### 容器与编排

| 名称 | 描述 | 链接 |
|------|------|------|
| **kubernetes** | K8s集群 | [containers/kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) |
| **docker** | Docker管理 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **helm** | Helm包管理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **openshift** | OpenShift | [GitHub](https://github.com/mcp-get/community-servers) |
| **rancher** | Rancher | [GitHub](https://github.com/mcp-get/community-servers) |
| **istio** | Istio服务网格 | [GitHub](https://github.com/mcp-get/community-servers) |
| **argo** | ArgoCD/Workflows | [GitHub](https://github.com/mcp-get/community-servers) |
| **knative** | Knative Serverless | [GitHub](https://github.com/mcp-get/community-servers) |

### 基础设施

| 名称 | 描述 | 链接 |
|------|------|------|
| **terraform** | 基础设施 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **pulumi** | Pulumi IaC | [GitHub](https://github.com/mcp-get/community-servers) |
| **ansible** | Ansible配置 | [GitHub](https://github.com/mcp-get/community-servers) |
| **cloudformation** | AWS CloudFormation | [GitHub](https://github.com/mcp-get/community-servers) |
| **serverless** | Serverless Framework | [GitHub](https://github.com/mcp-get/community-servers) |
| **vagrant** | Vagrant | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🤖 AI-ML - 人工智能/机器学习

### LLM服务

| 名称 | 描述 | 链接 |
|------|------|------|
| **openai** | OpenAI API | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **anthropic** | Anthropic API | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **google-ai** | Google AI | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **azure-openai** | Azure OpenAI | [GitHub](https://github.com/mcp-get/community-servers) |
| **cohere** | Cohere API | [GitHub](https://github.com/mcp-get/community-servers) |
| **mistral** | Mistral AI | [GitHub](https://github.com/mcp-get/community-servers) |
| **groq** | Groq API | [GitHub](https://github.com/mcp-get/community-servers) |
| **together** | Together AI | [GitHub](https://github.com/mcp-get/community-servers) |
| **fireworks** | Fireworks AI | [GitHub](https://github.com/mcp-get/community-servers) |
| **perplexity** | Perplexity API | [GitHub](https://github.com/mcp-get/community-servers) |
| **ai21** | AI21 Labs | [GitHub](https://github.com/mcp-get/community-servers) |
| **replicate** | Replicate | [GitHub](https://github.com/mcp-get/community-servers) |

### 本地模型

| 名称 | 描述 | 链接 |
|------|------|------|
| **ollama** | 本地模型 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **lmstudio** | LM Studio | [GitHub](https://github.com/mcp-get/community-servers) |
| **localai** | LocalAI | [GitHub](https://github.com/mcp-get/community-servers) |
| **text-generation-webui** | Oobabooga | [GitHub](https://github.com/mcp-get/community-servers) |
| **koboldcpp** | KoboldCPP | [GitHub](https://github.com/mcp-get/community-servers) |
| **llamafile** | Llamafile | [GitHub](https://github.com/mcp-get/community-servers) |

### ML平台

| 名称 | 描述 | 链接 |
|------|------|------|
| **huggingface** | HuggingFace | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **langchain** | LangChain | [GitHub](https://github.com/mcp-get/community-servers) |
| **langgraph** | LangGraph | [GitHub](https://github.com/mcp-get/community-servers) |
| **llamaindex** | LlamaIndex | [GitHub](https://github.com/mcp-get/community-servers) |
| **haystack** | Haystack | [GitHub](https://github.com/mcp-get/community-servers) |
| **semantic-kernel** | Semantic Kernel | [GitHub](https://github.com/mcp-get/community-servers) |
| **mlflow** | MLflow | [GitHub](https://github.com/mcp-get/community-servers) |
| **weights-biases** | W&B | [GitHub](https://github.com/mcp-get/community-servers) |
| **comet** | Comet ML | [GitHub](https://github.com/mcp-get/community-servers) |
| **neptune** | Neptune | [GitHub](https://github.com/mcp-get/community-servers) |
| **tensorboard** | TensorBoard | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🛠️ Development - 开发工具

### IDE集成

| 名称 | 描述 | 链接 |
|------|------|------|
| **vscode** | VSCode集成 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **neovim** | Neovim集成 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **jetbrains** | JetBrains IDE | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **sublime** | Sublime Text | [GitHub](https://github.com/mcp-get/community-servers) |
| **vim** | Vim集成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **emacs** | Emacs集成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **zed** | Zed编辑器 | [GitHub](https://github.com/mcp-get/community-servers) |

### 开发服务

| 名称 | 描述 | 链接 |
|------|------|------|
| **sentry** | 错误追踪 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **stripe** | 支付集成 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **posthog** | 产品分析 | [GitHub](https://github.com/mcp-get/community-servers) |
| **segment** | 数据收集 | [GitHub](https://github.com/mcp-get/community-servers) |
| **mixpanel** | 用户分析 | [GitHub](https://github.com/mcp-get/community-servers) |
| **amplitude** | 产品智能 | [GitHub](https://github.com/mcp-get/community-servers) |
| **launchdarkly** | 功能开关 | [GitHub](https://github.com/mcp-get/community-servers) |
| **split** | A/B测试 | [GitHub](https://github.com/mcp-get/community-servers) |
| **rollbar** | 错误监控 | [GitHub](https://github.com/mcp-get/community-servers) |
| **bugsnag** | 错误追踪 | [GitHub](https://github.com/mcp-get/community-servers) |
| **datadog** | 监控APM | [GitHub](https://github.com/mcp-get/community-servers) |
| **newrelic** | 性能监控 | [GitHub](https://github.com/mcp-get/community-servers) |

### CI/CD

| 名称 | 描述 | 链接 |
|------|------|------|
| **github-actions** | GitHub Actions | [GitHub](https://github.com/mcp-get/community-servers) |
| **gitlab-ci** | GitLab CI | [GitHub](https://github.com/mcp-get/community-servers) |
| **jenkins** | Jenkins | [GitHub](https://github.com/mcp-get/community-servers) |
| **circleci** | CircleCI | [GitHub](https://github.com/mcp-get/community-servers) |
| **travis** | Travis CI | [GitHub](https://github.com/mcp-get/community-servers) |
| **azure-pipelines** | Azure Pipelines | [GitHub](https://github.com/mcp-get/community-servers) |
| **bitbucket-pipelines** | Bitbucket Pipelines | [GitHub](https://github.com/mcp-get/community-servers) |
| **drone** | Drone CI | [GitHub](https://github.com/mcp-get/community-servers) |
| **teamcity** | TeamCity | [GitHub](https://github.com/mcp-get/community-servers) |
| **bamboo** | Bamboo | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 📦 Utilities - 实用工具

| 名称 | 描述 | 链接 |
|------|------|------|
| **time** | 时间工具 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **memory** | 知识图谱 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **calculator** | 计算器 | [GitHub](https://github.com/mcp-get/community-servers) |
| **converter** | 单位转换 | [GitHub](https://github.com/mcp-get/community-servers) |
| **qr-code** | 二维码生成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **barcode** | 条形码 | [GitHub](https://github.com/mcp-get/community-servers) |
| **uuid** | UUID生成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **hash** | 哈希计算 | [GitHub](https://github.com/mcp-get/community-servers) |
| **json** | JSON处理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **yaml** | YAML处理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **xml** | XML处理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **csv** | CSV处理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **regex** | 正则表达式 | [GitHub](https://github.com/mcp-get/community-servers) |
| **diff** | 文本对比 | [GitHub](https://github.com/mcp-get/community-servers) |
| **formatter** | 代码格式化 | [GitHub](https://github.com/mcp-get/community-servers) |
| **linter** | 代码检查 | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 💬 Communication - 通讯工具

| 名称 | 描述 | 链接 |
|------|------|------|
| **slack** | Slack集成 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **discord** | Discord集成 | [GitHub](https://github.com/mcp-get/community-servers) |
| **teams** | Microsoft Teams | [GitHub](https://github.com/mcp-get/community-servers) |
| **telegram** | Telegram | [GitHub](https://github.com/mcp-get/community-servers) |
| **whatsapp** | WhatsApp | [GitHub](https://github.com/mcp-get/community-servers) |
| **line** | LINE | [GitHub](https://github.com/mcp-get/community-servers) |
| **wechat** | 微信 | [GitHub](https://github.com/mcp-get/community-servers) |
| **dingtalk** | 钉钉 | [GitHub](https://github.com/mcp-get/community-servers) |
| **feishu** | 飞书 | [GitHub](https://github.com/mcp-get/community-servers) |
| **email** | 邮件服务 | [GitHub](https://github.com/mcp-get/community-servers) |
| **sendgrid** | SendGrid邮件 | [GitHub](https://github.com/mcp-get/community-servers) |
| **mailgun** | Mailgun | [GitHub](https://github.com/mcp-get/community-servers) |
| **twilio** | 短信/电话 | [GitHub](https://github.com/mcp-get/community-servers) |
| **zoom** | Zoom会议 | [GitHub](https://github.com/mcp-get/community-servers) |
| **meet** | Google Meet | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🔍 Search - 搜索服务

| 名称 | 描述 | 链接 |
|------|------|------|
| **brave-search** | Brave搜索 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **google-search** | Google搜索 | [GitHub](https://github.com/mcp-get/community-servers) |
| **bing-search** | Bing搜索 | [GitHub](https://github.com/mcp-get/community-servers) |
| **duckduckgo** | DuckDuckGo | [GitHub](https://github.com/mcp-get/community-servers) |
| **serpapi** | SERP API | [GitHub](https://github.com/mcp-get/community-servers) |
| **tavily** | Tavily搜索 | [GitHub](https://github.com/mcp-get/community-servers) |
| **exa** | Exa搜索 | [GitHub](https://github.com/mcp-get/community-servers) |
| **you-search** | You.com | [GitHub](https://github.com/mcp-get/community-servers) |
| **perplexity** | Perplexity | [GitHub](https://github.com/mcp-get/community-servers) |
| **algolia** | Algolia搜索 | [GitHub](https://github.com/mcp-get/community-servers) |
| **elasticsearch** | ES搜索 | [GitHub](https://github.com/mcp-get/community-servers) |
| **meilisearch** | Meilisearch | [GitHub](https://github.com/mcp-get/community-servers) |
| **typesense** | Typesense | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 📊 Monitoring - 监控服务

| 名称 | 描述 | 链接 |
|------|------|------|
| **prometheus** | Prometheus | [GitHub](https://github.com/mcp-get/community-servers) |
| **grafana** | Grafana | [GitHub](https://github.com/mcp-get/community-servers) |
| **datadog** | Datadog | [GitHub](https://github.com/mcp-get/community-servers) |
| **newrelic** | New Relic | [GitHub](https://github.com/mcp-get/community-servers) |
| **sentry** | Sentry | [GitHub](https://github.com/mcp-get/community-servers) |
| **pagerduty** | PagerDuty | [GitHub](https://github.com/mcp-get/community-servers) |
| **opsgenie** | Opsgenie | [GitHub](https://github.com/mcp-get/community-servers) |
| **victorops** | VictorOps | [GitHub](https://github.com/mcp-get/community-servers) |
| **statuspage** | Statuspage | [GitHub](https://github.com/mcp-get/community-servers) |
| **uptime-robot** | UptimeRobot | [GitHub](https://github.com/mcp-get/community-servers) |
| **pingdom** | Pingdom | [GitHub](https://github.com/mcp-get/community-servers) |
| **site24x7** | Site24x7 | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🔒 Security - 安全服务

| 名称 | 描述 | 链接 |
|------|------|------|
| **snyk** | Snyk安全 | [GitHub](https://github.com/mcp-get/community-servers) |
| **sonarqube** | SonarQube | [GitHub](https://github.com/mcp-get/community-servers) |
| **vault** | HashiCorp Vault | [GitHub](https://github.com/mcp-get/community-servers) |
| **aws-secrets** | AWS Secrets | [GitHub](https://github.com/mcp-get/community-servers) |
| **azure-keyvault** | Azure Key Vault | [GitHub](https://github.com/mcp-get/community-servers) |
| **gcp-secret-manager** | GCP Secret Manager | [GitHub](https://github.com/mcp-get/community-servers) |
| **1password** | 1Password | [GitHub](https://github.com/mcp-get/community-servers) |
| **bitwarden** | Bitwarden | [GitHub](https://github.com/mcp-get/community-servers) |
| **lastpass** | LastPass | [GitHub](https://github.com/mcp-get/community-servers) |
| **auth0** | Auth0 | [GitHub](https://github.com/mcp-get/community-servers) |
| **okta** | Okta | [GitHub](https://github.com/mcp-get/community-servers) |
| **keycloak** | Keycloak | [GitHub](https://github.com/mcp-get/community-servers) |
| **letsencrypt** | Let's Encrypt | [GitHub](https://github.com/mcp-get/community-servers) |
| **cloudflare** | Cloudflare | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 📈 Data-Science - 数据科学

| 名称 | 描述 | 链接 |
|------|------|------|
| **jupyter** | Jupyter Notebook | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **pandas** | Pandas数据处理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **numpy** | NumPy计算 | [GitHub](https://github.com/mcp-get/community-servers) |
| **scipy** | SciPy科学计算 | [GitHub](https://github.com/mcp-get/community-servers) |
| **matplotlib** | Matplotlib绘图 | [GitHub](https://github.com/mcp-get/community-servers) |
| **seaborn** | Seaborn可视化 | [GitHub](https://github.com/mcp-get/community-servers) |
| **plotly** | Plotly交互图 | [GitHub](https://github.com/mcp-get/community-servers) |
| **tableau** | Tableau | [GitHub](https://github.com/mcp-get/community-servers) |
| **powerbi** | Power BI | [GitHub](https://github.com/mcp-get/community-servers) |
| **looker** | Looker | [GitHub](https://github.com/mcp-get/community-servers) |
| **metabase** | Metabase | [GitHub](https://github.com/mcp-get/community-servers) |
| **superset** | Apache Superset | [GitHub](https://github.com/mcp-get/community-servers) |
| **redash** | Redash | [GitHub](https://github.com/mcp-get/community-servers) |
| **mode** | Mode Analytics | [GitHub](https://github.com/mcp-get/community-servers) |
| **hex** | Hex | [GitHub](https://github.com/mcp-get/community-servers) |
| **deepnote** | Deepnote | [GitHub](https://github.com/mcp-get/community-servers) |
| **observable** | Observable | [GitHub](https://github.com/mcp-get/community-servers) |
| **kaggle** | Kaggle | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 💼 Business - 商业工具

| 名称 | 描述 | 链接 |
|------|------|------|
| **salesforce** | Salesforce CRM | [GitHub](https://github.com/mcp-get/community-servers) |
| **hubspot** | HubSpot | [GitHub](https://github.com/mcp-get/community-servers) |
| **zoho** | Zoho | [GitHub](https://github.com/mcp-get/community-servers) |
| **pipedrive** | Pipedrive | [GitHub](https://github.com/mcp-get/community-servers) |
| **freshsales** | Freshsales | [GitHub](https://github.com/mcp-get/community-servers) |
| **zendesk** | Zendesk | [GitHub](https://github.com/mcp-get/community-servers) |
| **freshdesk** | Freshdesk | [GitHub](https://github.com/mcp-get/community-servers) |
| **intercom** | Intercom | [GitHub](https://github.com/mcp-get/community-servers) |
| **crisp** | Crisp | [GitHub](https://github.com/mcp-get/community-servers) |
| **trello** | Trello | [GitHub](https://github.com/mcp-get/community-servers) |
| **asana** | Asana | [GitHub](https://github.com/mcp-get/community-servers) |
| **monday** | Monday.com | [GitHub](https://github.com/mcp-get/community-servers) |
| **clickup** | ClickUp | [GitHub](https://github.com/mcp-get/community-servers) |
| **notion** | Notion | [GitHub](https://github.com/mcp-get/community-servers) |
| **airtable** | Airtable | [GitHub](https://github.com/mcp-get/community-servers) |
| **jira** | Jira | [GitHub](https://github.com/mcp-get/community-servers) |
| **confluence** | Confluence | [GitHub](https://github.com/mcp-get/community-servers) |
| **linear** | Linear | [GitHub](https://github.com/mcp-get/community-servers) |
| **shortcut** | Shortcut | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🎬 Media - 媒体处理

| 名称 | 描述 | 链接 |
|------|------|------|
| **ffmpeg** | FFmpeg处理 | [GitHub](https://github.com/mcp-get/community-servers) |
| **imagemagick** | ImageMagick | [GitHub](https://github.com/mcp-get/community-servers) |
| **pillow** | Pillow图像 | [GitHub](https://github.com/mcp-get/community-servers) |
| **opencv** | OpenCV | [GitHub](https://github.com/mcp-get/community-servers) |
| **cloudinary** | Cloudinary | [GitHub](https://github.com/mcp-get/community-servers) |
| **imgix** | Imgix | [GitHub](https://github.com/mcp-get/community-servers) |
| **twilio-video** | Twilio视频 | [GitHub](https://github.com/mcp-get/community-servers) |
| **mux** | Mux视频 | [GitHub](https://github.com/mcp-get/community-servers) |
| **stream** | Stream视频 | [GitHub](https://github.com/mcp-get/community-servers) |
| **daily** | Daily.co | [GitHub](https://github.com/mcp-get/community-servers) |
| **agora** | Agora声网 | [GitHub](https://github.com/mcp-get/community-servers) |
| **100ms** | 100ms | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 🔌 IoT - 物联网

| 名称 | 描述 | 链接 |
|------|------|------|
| **mqtt** | MQTT协议 | [GitHub](https://github.com/mcp-get/community-servers) |
| **coap** | CoAP协议 | [GitHub](https://github.com/mcp-get/community-servers) |
| **home-assistant** | Home Assistant | [GitHub](https://github.com/mcp-get/community-servers) |
| **openhab** | openHAB | [GitHub](https://github.com/mcp-get/community-servers) |
| **tuya** | 涂鸦智能 | [GitHub](https://github.com/mcp-get/community-servers) |
| **smartthings** | SmartThings | [GitHub](https://github.com/mcp-get/community-servers) |
| **philips-hue** | Philips Hue | [GitHub](https://github.com/mcp-get/community-servers) |
| **xiaomi** | 小米IoT | [GitHub](https://github.com/mcp-get/community-servers) |
| **esphome** | ESPHome | [GitHub](https://github.com/mcp-get/community-servers) |
| **tasmota** | Tasmota | [GitHub](https://github.com/mcp-get/community-servers) |
| **zigbee2mqtt** | Zigbee2MQTT | [GitHub](https://github.com/mcp-get/community-servers) |
| **zwavejs** | Z-Wave JS | [GitHub](https://github.com/mcp-get/community-servers) |

---

## 📖 参考资料

- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) - 450+ MCP服务器
- [Best of MCP Servers](https://github.com/tolkonepiu/best-of-mcp-servers) - 排名列表
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers) - 官方仓库
- [MCP Community Servers](https://github.com/mcp-get/community-servers) - 社区服务器
- [MCP Documentation](https://modelcontextprotocol.io/) - 官方文档

---

## 🚀 快速开始

### 安装MCP服务器

```bash
# 使用npx安装
npx -y @modelcontextprotocol/server-filesystem

# 使用npm全局安装
npm install -g @modelcontextprotocol/server-filesystem
```

### 配置Claude Code

```bash
# 添加MCP服务器
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir

# 列出已安装的服务器
claude mcp list

# 测试服务器
claude mcp test filesystem
```

---

*持续更新中... 当前收集: 500+ MCP Servers*
