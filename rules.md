 Phase 1: Core Frameworks & Environment
The first step is choosing your build environment. Whether you want a managed platform or a local setup, start here.


Managed Setup: Gemini Enterprise Agent Platform API Setup – The essential mission control for all Google Cloud agent projects.
The Low-Code Path:Agent Builder Guide – Best for rapid development using managed orchestration, grounding, and enterprise data stores.
Developer SDK:Gemini Enterprise Agent Platform SDK for Python – The client library required for writing custom agent logic and handling tool calls.
Agent Starter Pack
You can get access to Google Cloud in two ways:

Sign up for a no-cost trial at cloud.google.com/free
Use an existing Google Cloud account and request $100 in credits: https://forms.gle/xfv9vQzfRfNCCVbG7 (approved within 1–5 business days, while supplies last)
 
🔗 Phase 2: Action Mechanisms & Data Connectivity
Agents need to "do" things and "know" things. Use these resources to give your agent agency over data and tools.

Core Action Mechanisms (Tool Use)
Agent Builder Extensions: Building & Managing Extensions – Use pre-built Google extensions or connect your managed agent to any external API.
Knowledge & Grounding
Agent Builder Data Stores: Agent Search and Agent Conversation Overview – Use this unified platform to index your PDFs, websites, or BigQuery tables and give your managed agent a "source of truth."
 
🧰 Phase 3: Partner Integration & Infrastructure
Click each link below for Partner-specific information and resources:

Arize
Elastic
Fivetran
GitLab
MongoDB
Dynatrace
 
🧠 Phase 4: Reasoning, State, & Logic Hosting
Complex missions require memory and a place for your code to live.

Managed Orchestration: Agent Runtime – A runtime for deploying Python-based agents (LangChain/LlamaIndex) built with Agent Builder or the SDK.
State & Secrets: Secret Manager – Securely store and retrieve API keys for your partner integrations.
 
🚀 Phase 5: Deployment & Safety

Agent Deployment: Agent Builder Deployment – Learn how to make your managed agent accessible via a web interface or API.
Custom Backend Hosting: Cloud Run Quickstart – The go-to for hosting your own agent backends or custom-built tool servers.
Safety & Guardrails:Gemini Enterprise Agent Platform Safety Settings – Configure filters to ensure your agent remains helpful and follows your defined constraints.
 

#mongodb reference
About MongoDB

Explore the power of MongoDB's intelligent data platform to build innovative AI-driven solutions for real-world impact. MongoDB Atlas serves as the unified operational foundation and persistent memory layer for modern AI and agentic workloads. By combining operational, vector, and semantic data on a single platform, it eliminates the fragmented stacks and memory barriers that hinder AI performance. Ultimately, it empowers businesses to build production-grade AI that reasons accurately while remaining completely framework-agnostic.

Resources

Load the sample Mflix Dataset: Quickly spin up sample data to kickstart your project, sample_mflix.embedded_movies already contains vector embeddings for Vector Search! Or BYO embedding model and dataset(Embedding model should be one of MongoDB provided or Google provided).
Data Modelling in MongoDB: Learn best practices for structuring your data.
MongoDB MCP Server: Explore MongoDB MCP server to connect your database to LLM. 
MongoDB Tools: Explore essential tools to optimize your development workflow.
MongoDB Aggregations: Master data processing and analysis with powerful aggregation pipelines.
MongoDB Atlas Search: Build lightning-fast search experiences directly within your database.
MongoDB Vector Search: Supercharge your apps with AI-driven search capabilities.
AI Learning Hub: Dive into AI with MongoDB—guides, tutorials, and more.
Voyage AI documentation: Learn how to use MongoDB Voyage AI to generate embeddings.

#elastic reference
About Elastic

Elastic, the Search AI Company, integrates its deep expertise in search technology with artificial intelligence to help everyone transform all of their data into answers, actions, and outcomes. Elastic's Search AI Platform — the foundation for its search, observability, and security solutions — is used by thousands of companies, including more than 50% of the Fortune 500. Learn more at elastic.co.

Build Gemini Agents capable of working with complex enterprise data
Making AI agents work with real-world, unstructured data can be challenging. Agents can interact with data, but are often inefficient, costly, and unreliable. Elastic Agent Builder provides the capabilities developers need to make their agents more effective:

Contextual retrieval across any enterprise data - MCP tools exposing hybrid semantic, keyword, and vector search over any data, structured or unstructured, with hosted models for embeddings, reranking, and LLMs so your agent always gets the most relevant context.
Leverage fast, scalable Elastic index as a context layer to store memory and insights, not just raw data - Write agent outputs, summaries, and enriched facts back into Elasticsearch so your agent builds on what it already knows, turning raw signals into retrievable intelligence over time.
Custom tools from your data using ES|QL - Define callable tools that wrap ES|QL queries and expose them over MCP, letting your agent search, filter, aggregate, and compute over your data as needed without custom code.
Workflow tools that reach across systems - Define tools that retrieve data and take action. Elastic Workflows can call APIs, write to systems of record, and orchestrate multi-step operations so your agent can take real actions. 
Workflows that call subagents - Orchestrate specialized subagents as steps within a larger workflow, each powered by its own dynamically loaded Skills, so you can manage context and cost.
How to Get Started
Sign up for Elastic Cloud Serverless: Get a free Elastic Cloud trial at cloud.elastic.co. Create a Serverless Elasticsearch project — infrastructure and scaling are fully managed, so you focus on your agent, not your cluster. Choose your preferred Google Cloud region.
You can also access Elastic directly through the Google Cloud Marketplace.
Enable Agent Builder: In your Elasticsearch Serverless project, enable Agent Builder from the Kibana UI. Full setup guide: Get started with Elastic Agent Builder.
Agent Builder ships with built-in search tools for agentic retrieval and a built-in MCP server — no extra configuration required to get your first tools exposed.
Connect Google Cloud Agent Builder via MCP: Point Google Cloud Agent Builder at the Elastic MCP server endpoint found in the Agent Builder Tools UI in Kibana. Authenticate using an Elasticsearch API key. Your Gemini-powered agent will immediately see all the tools you've defined in Elastic.
Reference architecture: Implementing an agentic reference architecture with Elastic Agent Builder and MCP
Load and enrich your data: Use Elastic's built-in connectors to pull in data from Google Drive, Confluence, SharePoint, GitHub, databases, and more — or index your own data directly. Elastic's ELSER semantic model runs automatically for hybrid search. As your agent generates insights, write them back into Elasticsearch to build your context layer.
Define your tools: Use Agent Builder's UI to create custom tools backed by ES|QL queries or semantic search. Define Workflows that retrieve data, call external APIs, and invoke subagents. Each tool you define is immediately available to your agent via MCP.
Elastic Agent Builder tool best practices: Tools documentation
Build, iterate, and submit: Test your agent in the Agent Builder playground or directly in Google Cloud Agent Builder. Submit with a public GitHub repo (open-source license required) and a ~3-minute demo video.
Resources
Documentation

Elastic Agent Builder — Get Started
Elastic Agent Builder — MCP Server
Elastic Agent Builder — Tools
ES|QL Language Reference
Elastic Serverless — Get Started
Semantic Search with Elasticsearch
Elasticsearch Labs Blogs

Elastic MCP server: Expose Agent Builder tools to any AI agent
Agent Builder: Elastic reference architecture and MCP guide
Agent Builder now GA: Ship context-driven agents in minutes
AI agent memory: Creating smart agents with Elasticsearch managed memory
MCP overview and emerging use cases
How to build an MCP server with Elasticsearch
A2A Protocol and MCP: When to use which in Elasticsearch
Build task-aware agents with an expanded model catalog on Elastic Inference Service (EIS)
The Gemini CLI extension for Elasticsearch with tools and skills
Elastic and Google Cloud's powerful partnership in 2025
Tutorials and Notebooks

Elasticsearch Labs — Tutorials
Elasticsearch Labs — Notebooks on GitHub
Vector Search using Gemini Embeddings and Elasticsearch
Question Answering using Gemini, LangChain, and Elasticsearch
Get Access


Elastic Cloud Free Trial (Serverless)
Elastic on Google Cloud Marketplace
 
Connect with Elastic
Technical questions during the hackathon: Post in the hackathon discussion forum or reach out via the Devpost Discord
Community: discuss.elastic.co
Elastic on Discord: ela.st/discord

#arize reference
About Arize
Arize is the single platform built to help you accelerate development of AI apps and agents – then perfect them in production. Arize AX is an AI engineering platform focused on evaluation and observability. It helps AI engineers and AI product managers develop, evaluate, iterate and observe and monitor AI applications and agents. Arize helps enterprises increase their speed in building AI agents and ensure effectiveness for those outcomes that they can trust in production environments.

Build Gemini Agents with Full Observability and Self-Introspection via MCP
Ship agents that do more than run.  Ship agents that can self improve. With Arize Phoenix, your Gemini-powered agent gets production-grade tracing from day one, plus the ability to query its own traces, prompts, datasets, and experiments as tools at runtime via the Phoenix MCP server. Every decision your agent makes becomes inspectable, evaluable, and improvable.

We'll evaluate submissions based on technical implementation, meaningful use of tracing and MCP, quality of the agent's self-improvement loop, and overall impact.

Here are some guidelines to get you started:

The Arize track requires a code-owned agent runtime — Gemini CLI, Gemini Enterprise Agent Platform SDK, Google ADK, Agent Runtime, or Cloud Run. The visual Agent Builder alone is not supported for tracing integration. You must be able to instrument your code directly.
Instrument your agent with OpenInference. Auto-instrumentors exist for Google ADK, Agent Platform, Google GenAI, LangChain, LlamaIndex and many other frameworks.
Send traces to Phoenix Cloud (free SAAS) or self-hosted Phoenix
Configure the Phoenix MCP server in your agent so it can introspect its own operational data at runtime
Run evaluations on your traces with LLM-as-a-Judge or code evals to demonstrate quality
Bonus points for agents that use their own observability data to improve over time
How do I get started?
The fastest path is a free Phoenix Cloud account. Grab your API key, pip install an OpenInference instrumentor, and you're tracing in under five minutes. Phoenix is fully open-source, so you can also self-host if you prefer.

For the MCP integration, @arizeai/phoenix-mcp runs via npx and drops into any MCP client config — including Gemini CLI's settings.json.

Resources
Phoenix Cloud — Free tier, hosted Phoenix
Phoenix on GitHub — Open-source, self-hostable
Phoenix documentation — Tracing, evals, datasets, experiments, prompts
Phoenix MCP Server guide — Runtime introspection via MCP
OpenInference on GitHub — OpenTelemetry-compatible auto-instrumentors and utilities
Instrumentors for Gemini / Agent Platform / ADK:
openinference-instrumentation-google-adk — For Google ADK agents
openinference-instrumentation-vertexai — For Gemini Enterprise Agent Platform SDK and Gemini via generative_models
openinference-instrumentation-google-genai — For the unified google-genai SDK
Quickstarts: get up and running fast
https://github.com/Arize-ai/gemini-hackathon — End-to-end example: traced Gemini agent + Phoenix MCP + evaluations
Agent Platform (Gemini) tracing guide — Step-by-step setup
Phoenix LLM-as-a-Judge evals — Add evaluation pipelines to your submission