# LeetCode Mapper 🎯

A RAG-powered service that maps any algorithm problem statement to its closest LeetCode equivalent — with structured reasoning explaining why the match was made.

Built to solve a real personal pain point: manually mapping GFG problems to LeetCode equivalents while preparing a DSA study guide was tedious and time-consuming. This automates that process.

**Live Demo:** [Hugging Face Space](https://huggingface.co/spaces/SairamM3110/leetcode-mapper)  
**API:** [Swagger UI](https://leetcode-mapper.onrender.com/docs)  
**GitHub:** [leetcode-mapper](https://github.com/Sairam-M/leetcode-mapper)

---

## What It Does

Paste any algorithm problem statement — from GFG, an interview, or anywhere else — and get back:

- The closest LeetCode equivalent with a direct link
- Difficulty level and acceptance rate
- Relevant topic tags
- Structured reasoning: pattern, core constraint, why it matches, key difference, confidence level

---

## Architecture
## Architecture

```
Input Problem Statement
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  GPT-4o-mini — Query Normalisation                  │
│  strips output framing, extracts core algorithm     │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  text-embedding-3-small — Embed Normalised Input    │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  FAISS — Top 5 Nearest Neighbour Search             │
│  1420 LeetCode problems, pre-embedded at build time │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  GPT-4o-mini — Reranking + Reasoning                │
│  picks best conceptual match, generates explanation │
└─────────────────────────────────────────────────────┘
        │
        ▼
Structured Response
(title, link, difficulty, acceptance rate, topics, reasoning)
```

---

## Why Two LLM Calls

A single nearest neighbour retrieval was not enough. LeetCode and GFG frame the same problems differently — "check if a pair exists" vs "return indices of two numbers" are the same algorithm but embed far apart in vector space.

Two deliberate steps fix this:

**Query normalisation** — GPT-4o-mini strips output format differences and extracts the core algorithmic problem before embedding. This closes the framing gap.

**LLM reranking** — instead of blindly returning the top FAISS match, the top 5 candidates are passed to GPT-4o-mini which picks the most conceptually equivalent problem regardless of surface-level phrasing differences.

This retrieve-then-rerank pattern is a known RAG improvement over naive nearest neighbour retrieval.

---

## Why RAG Over Fine-Tuning

| | RAG | Fine-Tuning |
|---|---|---|
| Labelled training data needed | No | Yes — thousands of pairs |
| Corpus updatable | Yes — re-embed and reload | No — retrain from scratch |
| Explainability | Built in via reasoning layer | Black box |
| Cost | Low — inference only | High — training compute |
| Time to build | Days | Weeks |

Fine-tuning would require thousands of labelled GFG → LeetCode problem pairs. That data doesn't exist. RAG lets the embeddings do the heavy lifting with zero labelled data — the LLM reasons over retrieved candidates at inference time.

---

## Why FAISS Over a Vector Database

The corpus is 1420 problems — FAISS searches this in microseconds on a single machine with no server overhead. A vector database like Pinecone or Qdrant adds operational complexity (separate service, API, billing) that is not justified at this scale.

FAISS index is saved as a file, stored in AWS S3, and loaded into memory at startup. For production scale or metadata filtering requirements, pgvector or Qdrant would be the natural next step.

---

## Design Decisions and Tradeoffs

**Query normalisation adds latency (~1-2s) but significantly improves retrieval accuracy.** Without it, framing differences between GFG and LeetCode problem descriptions cause semantically identical problems to embed far apart.

**k=5 retrieval with reranking is more robust than k=1.** Single nearest neighbour retrieval failed on canonical problems like Two Sum. Reranking over 5 candidates with an LLM that understands algorithmic equivalence fixes this reliably.

**GPT-4o-mini over GPT-4o.** Sufficient reasoning quality at ~10x lower cost. Each request makes two LLM calls — normalisation and reranking — total cost under $0.001 per request.

**Problem statements with examples yield more accurate matches.** Examples provide additional semantic context during embedding. Abstract descriptions without examples occasionally produce weaker matches — noted as a known limitation.

**Rate limiting at 5 requests/minute per IP.** Each request triggers two paid OpenAI API calls. Rate limiting prevents cost abuse on the public endpoint.

---

## Tech Stack

- **FastAPI** — REST API with automatic Swagger UI
- **FAISS** — vector similarity search
- **OpenAI** — `text-embedding-3-small` for embeddings, `gpt-4o-mini` for normalisation and reranking
- **AWS S3** — stores FAISS index and dataset, downloaded at startup
- **Render** — API deployment
- **Gradio + Hugging Face Spaces** — demo UI
- **slowapi** — rate limiting

---

## Dataset

[LeetCode Problems Dataset](https://www.kaggle.com/datasets/gzipchrist/leetcode-problem-dataset) — 1,825 problems with full descriptions. Filtered to 1,420 algorithm problems after removing Database, Shell, Concurrency and other non-algorithm categories.

---

## Local Setup

```bash
git clone https://github.com/Sairam-M/leetcode-mapper
cd leetcode-mapper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
OPENAI_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

Run:
```bash
uvicorn app.main:app --reload
```

---

## Known Limitations

- Problem statements without examples occasionally yield weaker matches
- First request after cold start on free tier takes ~60 seconds (Render spinup + S3 download)
- Corpus limited to LeetCode algorithm problems — Database, Shell, Concurrency problems not included
- Rate limited to 5 requests/minute on the public endpoint

---

## Roadmap

- Phase 2: Parse Notion study guide, scrape GFG problem statements, batch map entire guide to LeetCode equivalents
- Phase 3: Enrich API responses with manually curated pattern labels from study guide
- Migrate deployment to AWS EC2 with S3 for full cloud-native setup
