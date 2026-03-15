---
name: rag-implementation
description: Retrieval-Augmented Generation pipeline design, chunking strategies, embedding models, vector stores, retrieval reranking, and production evaluation.
origin: ECC
---

# RAG Implementation

## When to Activate

- Building knowledge base search for LLM applications
- Implementing document retrieval for question-answering systems
- Designing chunking strategies for large document sets
- Selecting embedding models and vector stores
- Adding semantic search to existing systems
- Evaluating retrieval quality with RAGAS metrics
- Optimizing context assembly for token budget constraints

## RAG Pipeline Overview

```
Document → Chunk → Embed → Index → Query → Retrieve → Rerank → Assemble Context → LLM
Loading    Strategy Model   Store   Embed   Semantic   Score    Citation Track   Generate
```

## Chunking Strategies

### Fixed-Size Chunking (Simplest)

```python
def chunk_fixed(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

# Pros: Fast, predictable token count
# Cons: Breaks mid-sentence, loses context
```

> **Note — PII-Aware Chunking**
> Naive fixed-size chunking can split sensitive data across chunks
> (SSNs, credit card numbers, addresses routinely span boundaries).
> For PII-containing documents:
> 1. Use entity-aware chunking that keeps named entities intact
> 2. Tag PII chunks for access-controlled retrieval
> 3. Consider whether PII should be indexed at all

### Recursive Character Chunking (Better)

```python
def chunk_recursive(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split by sentences/paragraphs first, then fallback to character chunks."""
    separators = ["\n\n", "\n", ". ", " "]

    def split_by_separators(s: str, seps: list[str]) -> list[str]:
        if not seps:
            return [s] if s else []
        sep = seps[0]
        splits = s.split(sep)
        # Recursively split if any chunk > chunk_size
        return [chunk for split in splits for chunk in (
            split_by_separators(split, seps[1:]) if len(split) > chunk_size else [split]
        )]

    chunks = split_by_separators(text, separators)
    # Post-process: merge small chunks, add overlap
    merged = []
    for chunk in chunks:
        if merged and len(merged[-1]) + len(chunk) < chunk_size:
            merged[-1] += sep + chunk
        else:
            merged.append(chunk)
    return merged

# Pros: Respects boundaries, better context
# Cons: Slight overhead vs fixed
```

### Semantic Chunking (Advanced)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

def chunk_semantic(text: str, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.5):
    """Split by semantic similarity breaks."""
    model = SentenceTransformer(model_name)
    sentences = text.split('. ')
    embeddings = model.encode(sentences)

    chunks = []
    current_chunk = [sentences[0]]

    for i in range(1, len(sentences)):
        similarity = np.dot(embeddings[i], embeddings[i-1])
        if similarity < threshold:  # Semantic break
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])

    chunks.append('. '.join(current_chunk) + '.')
    return chunks

# Pros: Respects semantic boundaries, minimal context loss
# Cons: Slower (embedding all sentences), requires tuning threshold
```

### Chunk Size & Overlap Trade-Offs

| Size | Overlap | Pros | Cons |
|------|---------|------|------|
| 128 tokens | 10% | Precise retrieval, cheap | Loses context, more calls |
| 512 tokens | 20% | Balance | Standard choice |
| 1024 tokens | 30% | Rich context | Expensive, may retrieve too much |

**Recommendation**: 512 tokens with 20% overlap = 102 token overlap.

## Embedding Models

### Local (No API calls)

```python
from sentence_transformers import SentenceTransformer

# Best general-purpose local model
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dims, fast
embeddings = model.encode(texts)

# Larger, better quality
model = SentenceTransformer("all-mpnet-base-v2")  # 768 dims

# Domain-specific
model = SentenceTransformer("all-domain-roberta-base")
```

### API-Based (Higher Quality)

```python
from openai import OpenAI

client = OpenAI()

# OpenAI text-embedding-3-small (best value)
response = client.embeddings.create(
    input="Your text here",
    model="text-embedding-3-small"  # 512 dims, $0.02/M tokens
)
embedding = response.data[0].embedding

# OpenAI text-embedding-3-large
response = client.embeddings.create(
    input="Your text here",
    model="text-embedding-3-large"  # 3072 dims, higher quality
)

# Cohere Embed (production-grade)
import cohere
co = cohere.Client(api_key="...")
embeddings = co.embed(
    texts=texts,
    model="embed-english-v3.0"  # 1024 dims
)
```

**Dimensionality tradeoff**: Higher dims = better accuracy but higher compute and storage cost.

> **CRITICAL: Embedding Model Versioning**
> All vectors MUST be generated by the same embedding model version.
> Different models produce INCOMPATIBLE vector spaces — queries silently return wrong results.
>
> Best practices:
> - Store model_name + model_version in every chunk's metadata
> - Model upgrades require full re-indexing of the entire corpus
> - Pin the embedding model version in your requirements/lockfile
> - Never mix vectors from different models in the same index

## Vector Stores

### pgvector (SQL-Native)

```python
import psycopg2
from pgvector.psycopg2 import register_vector

conn = psycopg2.connect("dbname=mydb user=postgres")
register_vector(conn)

# Create table with vector column
conn.execute("""
    CREATE TABLE documents (
        id SERIAL PRIMARY KEY,
        content TEXT,
        embedding vector(384),  -- Must match embedding model dims
        UNIQUE(id)
    );
    CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
""")

# Insert documents
conn.execute(
    "INSERT INTO documents (content, embedding) VALUES (%s, %s)",
    ("Document text", embedding_array)
)

# Search
results = conn.execute("""
    SELECT id, content, embedding <-> %s AS distance
      FROM documents
     ORDER BY distance
     LIMIT 5
""", (query_embedding,))

# Pros: SQL-native, scales to millions, ACID guarantees
# Cons: Requires PostgreSQL, IVFFlat tuning for large datasets
```

### Pinecone (Managed)

```python
import pinecone

pinecone.init(api_key="...", environment="prod-1")
index = pinecone.Index("documents")

# Upsert vectors
index.upsert([
    ("doc1", embedding_array, {"source": "file.pdf", "page": 1}),
])

# Query
results = index.query(query_embedding, top_k=5, include_metadata=True)

# Pros: Fully managed, scales effortlessly, metadata filtering
# Cons: Proprietary, higher cost, vendor lock-in
```

### Chroma (Local Dev)

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("documents")

# Add documents
collection.add(
    ids=["doc1", "doc2"],
    embeddings=[embed1, embed2],
    documents=["text1", "text2"],
    metadatas=[{"source": "file1.pdf"}, {"source": "file2.pdf"}]
)

# Query
results = collection.query(query_embeddings=[query_embed], n_results=5)

# Pros: Local, no infrastructure, simple API
# Cons: Not for production (in-memory), no ACID
```

### Weaviate (Hybrid)

```python
import weaviate

client = weaviate.Client("http://localhost:8080")

# Create class
client.schema.create_class({
    "class": "Document",
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "embedding", "dataType": ["number[]"]}
    ]
})

# Search hybrid (BM25 + vector)
response = client.query.get("Document").with_hybrid(
    query="search term",
    vector=query_embedding,
    alpha=0.5  # 50% keyword, 50% semantic
).do()

# Pros: Hybrid search (semantic + keyword), GraphQL, HNSW indexing
# Cons: More complex setup
```

## Retrieval Strategies

### Semantic Search (Cosine Similarity)

```python
from sklearn.metrics.pairwise import cosine_similarity

# Find most similar chunks
similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
top_indices = similarities.argsort()[-5:][::-1]
top_chunks = [chunks[i] for i in top_indices]
```

### Hybrid Search (Keyword + Semantic)

```python
def hybrid_search(query: str, chunks: list[str], embeddings, alpha: float = 0.5):
    """Combine BM25 keyword scores with semantic similarity."""
    # BM25 ranking
    bm25 = BM25Okapi([chunk.split() for chunk in chunks])
    keyword_scores = bm25.get_scores(query.split())

    # Semantic ranking
    query_embedding = model.encode(query)
    semantic_scores = cosine_similarity([query_embedding], embeddings)[0]

    # Weighted combination
    combined = alpha * semantic_scores + (1 - alpha) * keyword_scores
    top_indices = combined.argsort()[-5:][::-1]
    return [chunks[i] for i in top_indices]
```

### Maximal Marginal Relevance (MMR)

```python
def mmr_retrieval(query_embedding, chunk_embeddings: list, chunks: list[str], k: int = 5, lambda_: float = 0.5):
    """Retrieve diverse results; reduce redundancy."""
    retrieved = []
    similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
    remaining_indices = set(range(len(chunks)))

    for _ in range(k):
        # Score = relevance - diversity penalty
        best_idx = None
        best_score = -float('inf')

        for i in remaining_indices:
            relevance = similarities[i]
            # Penalty: how similar is this to already retrieved?
            diversity = 1 - max([cosine_similarity([chunk_embeddings[i]], [chunk_embeddings[j]])[0][0]
                                for j in [chunks.index(r) for r in retrieved]] + [0])
            score = lambda_ * relevance - (1 - lambda_) * diversity

            if score > best_score:
                best_score = score
                best_idx = i

        retrieved.append(chunks[best_idx])
        remaining_indices.remove(best_idx)

    return retrieved

# Pros: Reduces redundant results, improves diversity
# Cons: Slower (requires similarity matrix), tuning lambda_
```

## Reranking

### Cross-Encoder Reranking (Cohere Rerank)

```python
import cohere

co = cohere.Client(api_key="...")

# First-pass retrieval: 20 semantic results
top_20_chunks = semantic_search(query, chunks, embeddings, k=20)

# Rerank: top 5 by relevance score
reranked = co.rerank(
    model="rerank-english-v2.0",
    query=query,
    documents=top_20_chunks,
    top_n=5
)

final_chunks = [top_20_chunks[result.index] for result in reranked.results]

# Why reranking helps:
# - Semantic search: fast but less accurate
# - Cross-encoder: slow but highly accurate
# - Hybrid: speed + accuracy with 2 models
```

### FlashRank (Fast Local Reranking)

```python
from flashrank import Ranker

ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")  # Local, fast

# Rerank top candidates
results = ranker.rank(
    query=query,
    passages=[{"id": i, "text": chunk} for i, chunk in enumerate(top_20_chunks)],
    batch_size=32
)

top_5 = results[:5]

# Pros: Local, fast, no API cost
# Cons: Lower quality than Cohere's cross-encoder
```

## Context Assembly

### Relevance Filtering

```python
def assemble_context(query_embedding, chunks, embeddings, threshold: float = 0.5):
    """Only include chunks above relevance threshold."""
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    relevant = [chunk for chunk, sim in zip(chunks, similarities) if sim >= threshold]
    return "\n".join(relevant)
```

### Token Budget Management

```python
def assemble_context_with_budget(chunks: list[str], max_tokens: int = 2000, model: str = "gpt-3.5-turbo"):
    """Add chunks until token budget exhausted."""
    import tiktoken
    enc = tiktoken.encoding_for_model(model)

    context = ""
    token_count = 0

    for chunk in chunks:
        chunk_tokens = len(enc.encode(chunk))
        if token_count + chunk_tokens <= max_tokens:
            context += chunk + "\n"
            token_count += chunk_tokens
        else:
            break

    return context, token_count
```

### Citation Tracking

```python
def retrieve_with_citations(query: str, index, chunks_with_ids: list[tuple]):
    """Track which chunk each answer comes from."""
    results = index.query(query, top_k=5)

    citations = []
    context = ""
    for result in results:
        chunk_id = result['id']
        text = result['text']
        score = result['score']

        context += f"[{chunk_id}] {text}\n"
        citations.append((chunk_id, score))

    return context, citations  # Return citations with confidence scores
```

## Evaluation

### Retrieval Metrics (RAGAS)

```python
from ragas.metrics import context_precision, context_recall, faithfulness

# context_precision: % retrieved chunks relevant to question
precision = context_precision.score(
    reference_answer="Expected answer",
    retrieved_context="Retrieved chunks"
)  # Higher is better, 0-1

# context_recall: % reference context retrieved
recall = context_recall.score(
    reference_answer="Expected answer",
    retrieved_context="Retrieved chunks"
)  # Higher is better, 0-1

# faithfulness: % answer supported by context
faithfulness_score = faithfulness.score(
    answer="LLM generated answer",
    contexts=["Retrieved chunks"]
)  # Higher is better, 0-1
```

### Retrieval Recall@K

```python
def eval_recall_at_k(queries: list[str], ground_truth: dict[str, list[str]],
                     retrieved_results: dict[str, list[str]], k: int = 5):
    """What % of ground truth was retrieved in top-k results?"""
    recalls = []
    for query in queries:
        truth = set(ground_truth[query])
        retrieved = set(retrieved_results[query][:k])
        recall = len(truth & retrieved) / len(truth) if truth else 0
        recalls.append(recall)
    return sum(recalls) / len(recalls)
```

## Anti-Patterns

```python
# ANTI-PATTERN 1: No overlap between chunks
chunks = [text[0:512], text[512:1024], text[1024:1536]]
# Context breaks at boundaries; retrieval loses edges
# FIX: Use 20% overlap (102 tokens for 512-token chunks)

# ANTI-PATTERN 2: Embedding at query time from index
# Index generated a year ago; query embedding from fresh model
# Different models ≠ compatible vectors; poor retrieval
# FIX: Use same embedding model for both index and query; version it

# ANTI-PATTERN 3: No reranking, trusting retrieval
# Retrieved top-5 by similarity; answers are vague/irrelevant
# FIX: Add cross-encoder reranking for 10-20% better quality

# ANTI-PATTERN 4: Ignoring metadata filtering
# Retrieved chunks include outdated policies alongside current
# FIX: Filter by metadata (date_range, source, version) before retrieval

# ANTI-PATTERN 5: No citation tracking
# User can't verify where answer came from
# FIX: Return [source_id] for each context chunk; show in answer

# ANTI-PATTERN 6: Fixed token budget for all queries
# Complex question needs more context; simple question wastes tokens
# FIX: Adjust context budget by query complexity or use adaptive chunking
```

## Agent Support

- **ai-engineer** — LLM integration, prompt engineering for RAG queries
- **python-expert** — Efficient chunking and embedding code
- **typescript-expert** — Node.js RAG implementation
- **sql-expert** — PostgreSQL + pgvector setup and query optimization

## Skill References

- **prompt-engineering-patterns** — Few-shot prompts for RAG generation
- **vector-database-setup** — Detailed PostgreSQL, Pinecone, Weaviate setup
- **llm-evaluation** — RAGAS metrics and answer quality assessment
