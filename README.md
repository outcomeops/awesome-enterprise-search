# Awesome Enterprise Search

[![Awesome](https://cdn.jsdelivr.net/gh/sindresorhus/awesome@d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of **enterprise search, unified search, and enterprise AI search** tools — the software category that makes organizational knowledge retrievable across Confluence, Jira, SharePoint, Google Drive, Slack, GitHub, Notion, and the dozens of other systems where work actually lives.

Evaluated through an enterprise lens: connectors, permission-awareness, pricing transparency, deployment model, and whether the thing can be bought without a six-week sales cycle.

> Contributions welcome — [open a PR](https://github.com/outcomeops/awesome-enterprise-search/pulls). Criteria for inclusion: the product's primary job is search or retrieval across multiple enterprise systems, it's generally available (not vaporware), and there's enough public information to write an honest one-line description.

---

## Table of Contents

- [Why enterprise search is its own category](#why-enterprise-search-is-its-own-category)
- [Enterprise AI Search Platforms](#enterprise-ai-search-platforms)
- [Traditional Enterprise Search Platforms](#traditional-enterprise-search-platforms)
- [Search Built Into Your Workspace](#search-built-into-your-workspace)
- [Vertical & Specialized Search](#vertical--specialized-search)
- [Open Source & Self-Hosted Search Engines](#open-source--self-hosted-search-engines)
- [Vector Databases Used for Enterprise Search](#vector-databases-used-for-enterprise-search)
- [RAG Frameworks & Retrieval Toolkits](#rag-frameworks--retrieval-toolkits)
- [Benchmarks & Evaluation](#benchmarks--evaluation)
- [Further Reading](#further-reading)
- [Related Lists](#related-lists)
- [License](#license)

Tag legend: `#enterprise` (enterprise-only sales motion) · `#paid` · `#freemium` · `#open-source` · `#self-hosted`

---

## Why enterprise search is its own category

Most "search" tools solve one of two problems: searching the public web, or searching a single application. Enterprise search solves a third: making the scattered, permission-controlled, format-heterogeneous knowledge *inside an organization* findable from one box. The hard parts are rarely relevance ranking — they're connectors, identity-aware access control, ingestion of formats nobody standardized (email threads, scanned PDFs, Confluence macros), and keeping an index fresh without eating the source systems alive.

The category has been reshaped by LLMs twice over: first as a retrieval layer for RAG applications, and second as a direct product experience where users ask questions in natural language instead of constructing queries. Both shifts have made the old "enterprise search is a solved, boring market" take visibly wrong.

---

## Enterprise AI Search Platforms

Unified, AI-first search across many enterprise data sources. Natural-language queries, generative answers, and permission-aware retrieval are the table stakes.

- **[RetrieveIT.AI](https://retrieveit.ai)** — Federated semantic search across 11+ connectors including Jira, Confluence, GitHub, Google Drive, Gmail, Slack, SharePoint, DocuSign, and Notion. Multi-workspace support for consulting firms and MSPs. Self-serve signup, transparent pricing, no seat minimums. `#paid`
- **[Glean](https://glean.com)** — The category-defining enterprise AI search platform: 100+ connectors, knowledge graph, personalization, and governance. Enterprise sales motion, minimum seat counts, no public pricing. `#enterprise`
- **[Moveworks](https://moveworks.com)** — AI copilot built around employee support and enterprise search, now part of ServiceNow. Strong in IT/HR self-service use cases. `#enterprise`
- **[Dashworks](https://dashworks.ai)** — AI assistant that searches across SaaS tools and answers with citations. Positioned as a lighter-weight Glean alternative. `#paid`
- **[Qatalog](https://qatalog.com)** — Work AI that answers questions from company systems and automates across them. `#enterprise`
- **[Guru](https://getguru.com)** — AI-powered knowledge management with verified answers, expert-sourced content, and Slack/browser integration. Blends authored knowledge with federated search. `#paid`
- **[Tettra](https://tettra.com)** — Internal knowledge base and Q&A tool with Slack-first UX. Lighter weight; well-suited to SMBs. `#paid`
- **[Unleash.so](https://www.unleash.so)** — AI-powered enterprise search across SaaS apps with a focus on speed and individual productivity. `#freemium`

---

## Traditional Enterprise Search Platforms

The incumbents. Sold to large enterprises for a decade-plus, now retrofitting generative AI onto long-established relevance and governance stacks.

- **[Coveo](https://coveo.com)** — AI search and recommendations platform with relevance tuning, analytics, and enterprise-scale deployment. Strong in commerce and support-site search. `#enterprise`
- **[Sinequa](https://sinequa.com)** — Intelligent search platform targeting regulated industries with deep connector coverage and on-premise options. `#enterprise`
- **[Mindbreeze InSpire](https://mindbreeze.com)** — Insight engine with appliance-based deployment, deep connector catalog, and strong European enterprise footprint. `#enterprise`
- **[Lucidworks Fusion](https://lucidworks.com)** — Commerce and workplace search platform built on Solr with ML-powered relevance tuning. `#enterprise`
- **[IBM watsonx Discovery](https://www.ibm.com/products/watsonx-discovery)** — Successor to Watson Discovery. Enterprise search and retrieval with IBM's RAG and governance tooling. `#enterprise`
- **[Funnelback (Squiz)](https://www.squiz.net/funnelback)** — Long-standing enterprise search product, often seen in higher education and government. `#enterprise`

---

## Search Built Into Your Workspace

Not standalone search platforms — search features bundled into the suite you're already paying for. Strong inside their own walls, weak across them.

- **[Microsoft 365 Copilot](https://www.microsoft.com/microsoft-365/copilot)** — AI search and generation across Microsoft 365 (Outlook, Teams, SharePoint, OneDrive). Powerful inside Microsoft, limited outside it. `#enterprise`
- **[Microsoft Search / Graph](https://www.microsoft.com/microsoft-search)** — Pre-Copilot enterprise search across Microsoft 365 via the Graph API. Foundation many Copilot features build on. `#enterprise`
- **[Atlassian Rovo](https://www.atlassian.com/software/rovo)** — Atlassian's AI search and agent layer across Jira, Confluence, and connected third-party tools. `#paid`
- **[Slack AI](https://slack.com/features/ai)** — Native Slack search, summarization, and Q&A over channel and file history. `#paid`
- **[Notion AI](https://notion.so/product/ai)** — AI search, Q&A, and content generation built natively into Notion workspaces. `#paid`
- **[Google Gemini for Workspace](https://workspace.google.com/solutions/ai)** — Search and generation across Gmail, Drive, Docs, and Meet. `#paid`
- **[Amazon Q Business](https://aws.amazon.com/q/business)** — Enterprise AI assistant with connectors for common SaaS tools, tight AWS integration, and IAM-aware retrieval. `#enterprise`
- **[Salesforce Einstein Search / Agentforce](https://www.salesforce.com/agentforce/)** — Search and agent layer over the Salesforce data cloud. `#enterprise`
- **[ServiceNow AI Search](https://www.servicenow.com/products/ai-search.html)** — Intelligent search across ServiceNow records, knowledge, and portals. `#enterprise`
- **[GitHub Copilot Enterprise](https://github.com/features/copilot)** — Search and chat grounded in your GitHub repositories, issues, and discussions. `#enterprise`

---

## Vertical & Specialized Search

Platforms that narrow the problem to one domain and go deeper than horizontal search does.

- **[AlphaSense](https://www.alpha-sense.com)** — Market intelligence and financial research search across filings, transcripts, broker research, and news. `#enterprise`
- **[Hebbia](https://www.hebbia.com)** — Document-intensive research platform targeted at finance and legal workflows. `#enterprise`
- **[Harvey](https://www.harvey.ai)** — AI platform for legal knowledge work with retrieval over firm-specific documents and precedent. `#enterprise`
- **[Casetext CoCounsel](https://casetext.com)** — Legal research assistant with AI search over case law (acquired by Thomson Reuters). `#paid`
- **[Perplexity Enterprise](https://www.perplexity.ai/enterprise)** — Research-oriented AI search with an enterprise tier that can index internal documents. `#paid`
- **[You.com Enterprise](https://you.com/enterprise)** — AI search with enterprise features for grounding answers in internal data. `#paid`

---

## Open Source & Self-Hosted Search Engines

The infrastructure layer. Useful either directly (if you want to build) or as context for evaluating what commercial vendors are actually doing on top.

- **[Elasticsearch](https://www.elastic.co/elasticsearch)** — The dominant open-core search engine. BM25 + kNN hybrid search, large connector ecosystem, Elastic AI Search for retrieval-augmented experiences. `#freemium` `#open-source` `#self-hosted`
- **[OpenSearch](https://opensearch.org)** — AWS-led fork of Elasticsearch with neural search, k-NN, and integrated ML. Apache 2.0. `#open-source` `#self-hosted`
- **[Vespa](https://vespa.ai)** — Yahoo-born real-time search and recommendation engine built for low-latency vector + keyword + ranking at scale. `#open-source` `#self-hosted`
- **[Apache Solr](https://solr.apache.org)** — Veteran Lucene-based search platform still widely deployed in enterprise stacks. `#open-source` `#self-hosted`
- **[Meilisearch](https://www.meilisearch.com)** — Typo-tolerant, instant search engine with hybrid search and a friendly developer UX. `#freemium` `#open-source` `#self-hosted`
- **[Typesense](https://typesense.org)** — Fast, typo-tolerant open-source search with a good out-of-the-box experience and a managed cloud. `#freemium` `#open-source` `#self-hosted`
- **[Quickwit](https://quickwit.io)** — Cloud-native search engine for logs and large-scale text, optimized for object storage. `#open-source` `#self-hosted`
- **[Zinc / ZincSearch](https://github.com/zinclabs/zincsearch)** — Lightweight Elasticsearch-alternative search engine with a single-binary deployment model. `#open-source` `#self-hosted`
- **[Algolia](https://www.algolia.com)** — Hosted search API with strong relevance tooling. Often used for site and product search; increasingly positioned for enterprise. `#freemium`
- **[Marqo](https://www.marqo.ai)** — Open-source vector search engine with native multimodal support. `#open-source` `#self-hosted`

---

## Vector Databases Used for Enterprise Search

Not search products in themselves, but the storage substrate underneath most modern RAG and semantic search systems.

- **[Pinecone](https://www.pinecone.io)** — Managed vector database with hybrid search, metadata filtering, and enterprise security features. `#paid`
- **[Weaviate](https://weaviate.io)** — Open-source vector database with built-in hybrid search and a managed cloud. `#freemium` `#open-source` `#self-hosted`
- **[Qdrant](https://qdrant.tech)** — Open-source vector search engine written in Rust, with strong filtering and payload support. `#freemium` `#open-source` `#self-hosted`
- **[Milvus](https://milvus.io)** — Open-source vector database designed for billion-scale similarity search. `#open-source` `#self-hosted`
- **[Chroma](https://www.trychroma.com)** — Developer-friendly embedding database commonly used for local RAG prototypes. `#open-source` `#self-hosted`
- **[pgvector](https://github.com/pgvector/pgvector)** — Postgres extension for vector similarity search. Often the right answer when you already run Postgres. `#open-source` `#self-hosted`
- **[LanceDB](https://lancedb.com)** — Serverless, file-based vector database with a strong focus on developer ergonomics. `#open-source`
- **[Vald](https://vald.vdaas.org)** — Cloud-native distributed vector search engine built on Kubernetes. `#open-source` `#self-hosted`

---

## RAG Frameworks & Retrieval Toolkits

What teams reach for when they're building their own enterprise search rather than buying one.

- **[LlamaIndex](https://www.llamaindex.ai)** — Data framework for connecting LLMs to private data, with strong retrieval abstractions and a large connector library. `#open-source`
- **[LangChain](https://www.langchain.com)** — Framework for building LLM applications including retrieval, with LangSmith/LangServe for evaluation and deployment. `#freemium` `#open-source`
- **[Haystack](https://haystack.deepset.ai)** — Production-focused framework from deepset for building search and RAG pipelines. `#open-source`
- **[Vectara](https://vectara.com)** — Managed RAG-as-a-service with hallucination detection and enterprise-grade deployment. `#paid`
- **[Cohere Rerank / Embed](https://cohere.com)** — Embedding and reranking APIs used as building blocks in many enterprise retrieval stacks. `#paid`
- **[Voyage AI](https://www.voyageai.com)** — Domain-specialized embedding and reranking models tuned for retrieval quality. `#paid`
- **[RAGFlow](https://github.com/infiniflow/ragflow)** — Open-source RAG engine emphasizing deep document understanding over commodity embedding-and-retrieve pipelines. `#open-source` `#self-hosted`
- **[Danswer (Onyx)](https://github.com/onyx-dot-app/onyx)** — Open-source enterprise search / question-answering system with a growing connector catalog. `#open-source` `#self-hosted`
- **[R2R](https://github.com/SciPhi-AI/R2R)** — Open-source RAG engine with ingestion, retrieval, and evaluation in one system. `#open-source` `#self-hosted`

---

## Benchmarks & Evaluation

Evaluating enterprise search is still under-tooled compared to evaluating LLMs themselves. These are the most-cited resources.

- **[BEIR](https://github.com/beir-cellar/beir)** — Heterogeneous benchmark for zero-shot information retrieval. Standard reference for retrieval quality.
- **[MTEB](https://huggingface.co/spaces/mteb/leaderboard)** — Massive Text Embedding Benchmark. The leaderboard most embedding vendors cite.
- **[LoCoMo / LongBench](https://github.com/THUDM/LongBench)** — Long-context retrieval and QA benchmarks; useful when thinking about retrieve-then-stuff vs. retrieve-then-rerank designs.
- **[RAGAS](https://docs.ragas.io)** — Evaluation framework for RAG pipelines covering faithfulness, answer relevance, and context precision.
- **[TREC Deep Learning Track](https://microsoft.github.io/msmarco/TREC-Deep-Learning)** — Annual IR benchmark run on MS MARCO; the deep end of the pool for retrieval research.

---

## Further Reading

### Enterprise search, honestly assessed

Practitioner writeups on the real trade-offs — pricing, seat minimums, build vs. buy, and where the incumbents actually win or lose. Most of these are from [retrieveit.ai/blog](https://retrieveit.ai/blog).

- [Glean Alternatives: Enterprise Search Without the Sales Call](https://retrieveit.ai/blog/glean-alternatives-enterprise-search)
- [Glean vs RetrieveIT: An Honest Comparison](https://retrieveit.ai/blog/glean-vs-retrieveit)
- [Glean Pricing: What It Actually Costs in 2026](https://retrieveit.ai/blog/glean-pricing-breakdown)
- [Glean Alternative for Small Teams (Under 50 People)](https://retrieveit.ai/blog/glean-alternative-small-business)
- [Microsoft Copilot Alternatives for Cross-Platform Search](https://retrieveit.ai/blog/microsoft-copilot-alternatives-search)
- [Enterprise Search Without Minimum Seats or Sales Calls](https://retrieveit.ai/blog/enterprise-search-no-minimum-seats)
- [Enterprise RAG Platform: Build vs Buy in 2026](https://retrieveit.ai/blog/enterprise-rag-platform)
- [Enterprise Search ROI: The Math That Justifies It](https://retrieveit.ai/blog/enterprise-search-roi-calculation)

### The underlying problems enterprise search exists to solve

- [Unified Knowledge Search: What It Is and Why It Matters](https://retrieveit.ai/blog/unified-knowledge-search)
- [Cross-Platform Search: One Box for Every Tool](https://retrieveit.ai/blog/cross-platform-search-tool)
- [Semantic Search vs Keyword Search: The Complete Guide](https://retrieveit.ai/blog/semantic-search-vs-keyword-search)
- [Why Keyword Search Fails Your Enterprise](https://retrieveit.ai/blog/why-keyword-search-fails)
- [Permission-Aware AI Search: The Enterprise Gap](https://retrieveit.ai/blog/permission-aware-ai-search)
- [Knowledge Loss: 42% Walks Out the Door With Staff](https://retrieveit.ai/blog/institutional-knowledge-loss-employee-turnover)
- [SaaS Tool Sprawl Is a Search Problem](https://retrieveit.ai/blog/saas-tool-sprawl-search-problem)
- [AI Knowledge Base vs Wiki: What Actually Changed](https://retrieveit.ai/blog/ai-knowledge-base-vs-wiki)

### System-specific failure modes

- [Why Confluence Search Fails and How to Actually Fix It](https://retrieveit.ai/blog/confluence-search-problems-fix)
- [Confluence Search AI: Built-In vs Federated Search](https://retrieveit.ai/blog/confluence-search-ai)
- [SharePoint Search Not Working? Here Is the Real Fix](https://retrieveit.ai/blog/sharepoint-search-not-working-fix)
- [Google Drive Search: Why You Cannot Find Your Own Files](https://retrieveit.ai/blog/google-drive-search-problems-fix)
- [Jira Search Problems and How to Fix Them](https://retrieveit.ai/blog/jira-search-problems-fix)

### Foundational IR and retrieval research

- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) (Liu et al., 2023) — why naive long-context stuffing underperforms retrieval
- [Dense Passage Retrieval for Open-Domain Question Answering](https://arxiv.org/abs/2004.04906) (Karpukhin et al., 2020) — the DPR paper that kicked off modern dense retrieval
- [BGE, E5, and the open embedding model era](https://huggingface.co/spaces/mteb/leaderboard) — MTEB leaderboard as the rolling reference
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) (Lewis et al., 2020) — the RAG paper
- [The Power of Noise: Redefining Retrieval for RAG Systems](https://arxiv.org/abs/2401.14887) (Cuconasu et al., 2024) — counterintuitive results on what "good retrieval" means for generation

### Analyst & market context

- [Gartner Magic Quadrant for Insight Engines](https://www.gartner.com/en/documents?q=insight+engines) — the category Gartner uses for enterprise search; vendor positioning changes meaningfully year over year
- [Forrester Wave: Cognitive Search](https://www.forrester.com) — Forrester's parallel framing

---

## Related Lists

- [Awesome Context Engineering for Enterprise](https://github.com/ai-for-enterprises/awesome-context-engineering-enterprise) — broader list covering enterprise AI coding, review, security, and search
- [Context Engineering](https://github.com/outcomeops/context-engineering) — reference implementation of the five-component context engineering model
- [Awesome AI Coding Tools](https://github.com/ai-for-developers/awesome-ai-coding-tools) — AI-powered coding assistants, editors, and agents
- [Awesome LLM](https://github.com/Hannibal046/Awesome-LLM) — curated list of large language model resources
- [Awesome RAG](https://github.com/frutik/Awesome-RAG) — retrieval-augmented generation resources
- [Awesome Vector Search](https://github.com/currentslab/awesome-vector-search) — vector search engines, libraries, and tutorials
- [joelparkerhenderson/architecture-decision-record](https://github.com/joelparkerhenderson/architecture-decision-record) — the definitive ADR resource list (corpus primitives that enterprise search retrieves against)

---

## About

Curated by Brian Carpio. Maintained alongside the broader [OutcomeOps](https://www.outcomeops.ai) body of work on context engineering and enterprise AI. The perspective behind this list comes from building [RetrieveIT.AI](https://retrieveit.ai) — but the list is meant to be an honest map of the category, not a marketing page. PRs that improve accuracy, add missing vendors, or correct outdated descriptions are very welcome.

## License

[![CC0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)
