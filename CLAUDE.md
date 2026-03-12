# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development
```bash
# Install dependencies
uv sync

# Add new dependencies
uv add <package-name>
uv add --dev <package-name>  # for dev dependencies
```

### Running the Application
```bash
# Run immediately (manual trigger)
uv run python src/main.py run                  # defaults to after_close
uv run python src/main.py run pre_market       # pre-market report (8:30 AM)
uv run python src/main.py run mid_close        # mid-day report (11:30 AM)
uv run python src/main.py run after_close      # after-close report (3:30 PM)

# Start scheduler (runs automatically at configured times)
uv run python src/main.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run unit tests only (exclude integration tests)
uv run pytest tests/ -v --ignore=tests/test_workflow_integration.py

# Run integration tests
uv run pytest tests/test_workflow_integration.py -v -m integration

# Run specific test
uv run pytest tests/unit/test_database.py -v
uv run pytest tests/test_workflow_graph.py -v
```

## Architecture Overview

This is a **financial daily report generation system** built with LangGraph. The core architecture is a state-based workflow graph where data flows through a series of nodes.

### LangGraph Workflow

The workflow is defined in `src/workflow/graph.py`:
```
collect → clean → analyze → store → vectorize → rag → [route] → generate → save
```

The `[route]` conditionally directs to one of three generation nodes based on `report_type`:
- `pre_market` → `pre_market_generate` (8:30 AM - market opening prediction)
- `mid_close` → `mid_close_generate` (11:30 AM - intraday summary)
- `after_close` → `after_close_generate` (3:30 PM - end-of-day analysis)

### State Definition (`src/workflow/state.py`)

`ReportState` is a TypedDict that flows through all nodes:
- `report_type`: Which report to generate
- `news_data`: Raw news from collectors
- `market_data`: Raw market data (indices, fund flows)
- `cleaned_news`: Processed news with extracted entities/sentiment
- `enriched_news`: Deep analysis results with event types and stock associations
- `context`: RAG-retrieved historical context
- `report`: Generated markdown report
- `errors`: Error list

**Key pattern**: Nodes must return `{**state, "new_field": value}` - they never mutate state in-place.

### News Processing Pipeline

**Collection** (`src/collectors/`):
- 6 sources via AKShare API: 东财, 新浪, 富途, 同花顺, 财联社

**Cleaning** (`src/processors/cleaner.py`):
1. `RuleCleaner`: HTML removal, deduplication (MD5 hash)
2. `LLMCleaner`: Entity extraction, sentiment analysis, importance scoring (1-5), tagging

**Deep Analysis** (`src/processors/analyzer.py`):
- `HeavyAnalyzer`: Event extraction (6 predefined types), stock association (direct/indirect/concepts), intelligent merging of same-stock news
- Adds `event_type`, `event_subtype`, `related_stocks` fields to enriched_news
- Merges multiple news about same stock into single entry
- Sorts by importance and stock relevance

Event types: 财报类, 重组并购类, 政策影响类, 经营类, 风险类, 其他

The cleaner extracts structured data per news item:
```python
{
    'entities': [],      # Company names, people, etc.
    'sentiment': '',     # positive/neutral/negative
    'importance': 3,     # 1-5 scale
    'tags': [],          # Industry/concept tags
    'is_trash': False    # Whether to filter out
}
```

The analyzer adds:
```python
{
    'event_type': '财报类',           # Event category
    'event_subtype': '财报发布',       # Specific event
    'related_stocks': {
        'direct': ['600519.SH:贵州茅台'],    # Direct stocks
        'indirect': ['白酒行业'],            # Industries
        'concepts': ['白酒概念', '消费龙头']  # Concepts
    }
}
```

### Report Generation (`src/workflow/nodes.py`)

Generation nodes use `_format_news_enriched()` which includes:
- Event type badges (e.g., [财报类], [政策影响类])
- Sentiment icons (📈 positive, ➡️ neutral, 📉 negative)
- Stock information (direct targets with codes)
- Importance ratings (1-5)
- Related concepts

The enriched data provides deeper context for LLM to generate more insightful reports.
- Passes only title + truncated content to LLM

Prompts are in `config/prompts.py`:
- `PRE_MARKET_PROMPT`: Focus on prediction, overnight US markets
- `MID_CLOSE_PROMPT`: Focus on intraday trends, sector flows
- `AFTER_CLOSE_PROMPT`: Focus on full-day analysis, fund flows

### RAG System (`src/rag/`)

- Vector storage: ChromaDB (`data/chroma_db`)
- Embeddings: Configurable (OpenAI/Ollama/vLLM)
- Retrieval: Uses first news title as query for historical context

### Storage (`src/storage/database.py`)

SQLite database (`data/financial.db`) with two tables:
- `news`: title, content, source, publish_time
- `reports`: report_date, report_type, content

## Configuration

Environment variables in `.env`:

**LLM (for generation and cleaning):**
```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_key
CHAT_MODEL=gpt-4o           # For report generation
CLEAN_MODEL=gpt-4o-mini     # For news cleaning
```

**Embedding (for RAG):**
```
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=your_key
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_TYPE=openai   # or "ollama" for Ollama/vLLM
```

**Schedule times:**
```
PRE_MARKET_TIME=08:30
MID_CLOSE_TIME=11:30
AFTER_CLOSE_TIME=15:30
```

Configuration is loaded in `config/settings.py` with dataclasses.

## Adding New Report Types

1. Add prompt template in `config/prompts.py`
2. Add generation node in `src/workflow/nodes.py`
3. Update `route_by_report_type()` in `src/workflow/nodes.py`
4. Add node to graph in `src/workflow/graph.py`

## Key Design Patterns

**Node immutability**: Always return new state, never mutate input
**Error resilience**: Nodes log errors but don't crash; workflow continues
**Testability**: Each node is independently testable; mocks used in integration tests
**Separation of concerns**: Collectors, processors, generators, storage are independent modules

## Entry Points

**Manual run**: `src/main.py` with `run` argument
**Scheduled run**: `src/main.py` without arguments starts `ReportScheduler` in `src/scheduler/cron_scheduler.py`
