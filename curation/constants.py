# Tunable constants for the curation pipeline.
# Edit here to adjust LLM/search behaviour without touching curate.py.

# --- LLM / API ---
DEFAULT_API_URL = "http://localhost:11434/v1/chat/completions"
DEFAULT_MODEL = "gemma3n:e4b"
DEFAULT_CONFIDENCE_THRESHOLD = 95

# --- Web search ---
DDG_MAX_RESULTS = 5          # DDG results fetched per source query
SNIPPET_CHAR_LIMIT = 1000     # Max chars kept from each DDG result set
SCORING_SNIPPET_CHARS = 500  # Max chars of each snippet shown to the scoring LLM

# --- Snippet filtering ---
SNIPPET_MATCH_THRESHOLD = 65  # Min match score (0-100) for a snippet to enter web_context

# --- Organic detection ---
ORGANIC_PHRASES = {"certified organic", "biodynamic", "certified biodynamic"}
