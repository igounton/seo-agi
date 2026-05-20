# CLAUDE.md

This is **seo-agi** -- a Claude Code skill for Generative Engine Optimization. It writes pages that rank on Google AND get cited by LLMs.

This is not a generic SEO prompt. It enforces 500-token chunk architecture, Reddit Test quality gates, verification tags, "Not For You" blocks, ICP-driven content targeting, and real competitive data from DataForSEO/Ahrefs/SEMRush/GSC.

## Structure

```
SKILL.md              -- The framework (GEO engine + data layer integration)
SPEC.md               -- Technical architecture for the data layer
scripts/
  research.py         -- CLI: SERP research via DataForSEO. v1.7.1 adds
                         meta_entities (bolded snippet phrases),
                         target_ngrams (top 3 competitor bigrams/trigrams),
                         primary_intent + secondary_intent dual mapping.
  gsc_pull.py         -- CLI: Google Search Console data
  tributary_gen.py    -- CLI: Generates Tier 1/Tier 2 companion content
                         (Google Sites, Medium, Subreddit, Google Sheets,
                         LinkedIn) topically derived from the money page's
                         500-token chunk architecture. See SKILL.md
                         "Tributary Trust Protocol" for the strategy.
  setup.py            -- Interactive first-run config
  lib/
    env.py            -- Config loader
    dataforseo.py     -- DataForSEO REST API client
    massive.py        -- Massive Web Render client (v1.9.0). Primary
                         competitor content parser when MASSIVE_API_TOKEN
                         is set. Returns clean markdown including
                         JS-loaded content. Per-URL fallback to
                         DataForSEO on failure.
    serp_analyze.py   -- Content gap analysis engine
    gsc_client.py     -- Google Search Console client
references/
  page-templates.md   -- Structural templates by page type
  schema-patterns.md  -- JSON-LD schema patterns
fixtures/             -- Mock data for testing without API calls
tests/                -- Unit tests
```

## The Framework (SKILL.md)

The SKILL.md is the living document. It contains:
- Core belief system (anti-generic, LLM retrieval, entity consensus)
- Google AI Search 7 ranking signals
- 500-token chunk architecture
- SEAT signals (Semantic + E-E-A-T + Entity/Knowledge Graph)
- Quality gates: Reddit Test, Prove-It Details, Not For You, Information Gain Test
- ICP (Ideal Customer Persona) requirement in every page brief
- Deep Entity History & Identity Tags for local trust signals
- Self-Placement Rule for listicles (objective #1 ranking with tradeoffs)
- Keyword Cannibalization governance (noindex for overlapping intents)
- **Tributary Trust Protocol**: AEO entity validation via owned Tier 1 assets
  (Google Sites, Medium, Subreddits, Google Sheets, LinkedIn). Quality gates
  apply equally to off-page content -- thin tributaries net-harm the money
  page's entity signal. Generated via `scripts/tributary_gen.py`.
- **Massive Web Render integration** (v1.9.0): competitor content
  parsing now flows through Massive when `MASSIVE_API_TOKEN` is set,
  with graceful per-URL fallback to DataForSEO. SERP and keyword data
  still come from DataForSEO -- Massive's search endpoint doesn't
  return organic results.
- **Gemini 3.5 Flash RAG Optimization** (v1.8.0): DOM Vectoring &
  Shard Extraction Compliance (critical data must live in front-facing
  `<table>` / RDFa, not just JSON-LD), Trust Pilot as Tier 1 tributary,
  Off-Page Schema Injection (Organization/Person schema on Cloud Pages
  and PRs linking to GBP CID to block NavBoost rank-shuffling),
  48-point checklist with new DOM-visible-data check.
- **LLM Retrieval & Substantive Content Protocols** (v1.7.1): Meta Entity
  Isolation (snippet-level entities), Bigram/Trigram AI Alignment (top
  3 competitor n-grams in AI Summary Nugget), Dual-Intent Mapping
  (Primary + Secondary action funnel), 410 Prune Protocol (explicit
  301/410 recommendations on rewrites), Technical Codebase Execution
  (semantic HTML injection + redirect config snippets when in-repo).
- Verification tagging system ({{VERIFY}}, {{RESEARCH NEEDED}}, {{SOURCE NEEDED}})
- Vertical-specific instructions (airport/parking, local service, listicle, comparison)
- LLM/AEO citation strategy
- Hub & spoke internal linking
- Execution protocol with data layer integration

## Running Tests

```bash
python3 tests/test_env.py
python3 tests/test_serp_analyze.py
python3 tests/test_dataforseo.py

# Mock mode research:
python3 scripts/research.py "test keyword" --mock
```

## Style

- No em dashes in any output
- No "nestled", no "in today's fast-paced world", no "whether you're a...or a..."
- Numbers and specifics over adjectives
- Every claim tagged with {{VERIFY}} or {{SOURCE NEEDED}}
- Tables are mandatory for comparisons -- never simulate with bullet points
