# Tunable constants for the curation pipeline.
# Edit here to adjust LLM/search behaviour without touching curate.py.

# --- Web sources ---
# UPC-capable sources are tried first when a SKU looks like a barcode.
CURATED_SOURCES = [
    # Wine databases — good for both name and UPC lookups
    {"name": "Wine Searcher",              "domain": "wine-searcher.com",    "upc_capable": True},
    {"name": "Vivino",                     "domain": "vivino.com",           "upc_capable": True},
    {"name": "CellarTracker",              "domain": "cellartracker.com",    "upc_capable": True},
    # Critic review sites — commented out (paywalled; DDG rarely returns useful snippets)
    # {"name": "Jeb Dunnuck",               "domain": "jebdunnuck.com"},
    # {"name": "James Suckling",             "domain": "jamessuckling.com"},
    # {"name": "Vinous",                     "domain": "vinous.com"},
    # {"name": "Robert Parker Wine Advocate","domain": "robertparker.com"},
    # {"name": "Wine Enthusiast",            "domain": "wineenthusiast.com"},
]

# --- LLM / API ---
DEFAULT_API_URL = "http://localhost:8080/v1/chat/completions"
DEFAULT_MODEL = "gemma3n:e4b"
DEFAULT_CONFIDENCE_THRESHOLD = 90

# --- Web search ---
DDG_MAX_RESULTS = 3          #  DDG results fetched per source query
SNIPPET_CHAR_LIMIT = 1500     # Max chars kept from each DDG result set
SCORING_SNIPPET_CHARS = 300  #  Max chars of each snippet shown to the scoring LLM
DDG_SLEEP_SECONDS = 0.2      #  Delay between DDG queries

# --- Snippet filtering ---
SNIPPET_MATCH_THRESHOLD = 85  # Min match score (0-100) for a snippet to enter web_context
TOP_N_SNIPPETS = 3            # Max number of top-scoring snippets passed to the tag-inference LLM

# --- Organic detection ---
ORGANIC_PHRASES = {"certified organic", "biodynamic", "certified biodynamic"}

# --- LLM prompts ---
BATCH_MATCH_SCORE_PROMPT = """\
You are a wine expert. Score how well each web snippet matches the wine product name below.

Product: {name}
Brand: {brand}

Abbreviation guide (expand these when comparing names):
PN / P.N. = Pinot Noir | PG = Pinot Gris or Pinot Grigio | SB = Sauvignon Blanc
CS / Cab / Cab Sauv = Cabernet Sauvignon | CF = Cabernet Franc | GR = Grenache
Chard = Chardonnay | Shiraz = Syrah (same grape, different name) | GSM = Grenache Shiraz Mourvèdre
Sauv Blanc = Sauvignon Blanc | Pinot Gris = Pinot Grigio | Tempranillo = Tinto

Snippets:
{snippets_block}

Score each snippet 0–100:
  90–100: clearly this exact wine — producer/brand, variety, and style all confirmed
  70–89:  very likely the same wine — most key details align
  50–69:  possibly the same wine — some details match but ambiguous
  30–49:  unlikely — only loose or coincidental similarity
  0–29:   different wine, wrong producer, or irrelevant content

Return ONLY a JSON object mapping snippet index (as string) to integer score.
Example: {{"0": 85, "1": 40, "2": 72}}
No explanation, no extra text."""

PROMPT_TEMPLATE = """\
You are a wine expert. Use the product information and the web context below to identify the wine's metadata.

Product name: {name}
Category: {category}
Brand: {brand}

Web context: {web_context}

Rules:
- is_blend is true if the wine contains more than one grape variety, false if it is a single varietal.
- organic is true only if the wine is certified organic, biodynamic, or explicitly marketed as certified biodynamic. Omit or set false if uncertain.
- If the web context contradicts the product name, trust the web context.
- confidence is an integer from 0 to 100 reflecting certainty that the tags are correct:
  - 90–100: two or more independent sources explicitly confirm producer, region, AND grape variety
  - 70–89:  one strong source confirms the producer name plus most key details
  - 50–69:  one source confirms region or grape but not both; or a weak match
  - 30–49:  no strong web source; details inferred from name and abbreviations only
  - 0–29:   no usable web context; pure guesswork
  Hard limits — do not exceed these regardless of how confident you feel:
  * Max 84 if only one source contributed to your answer
  * Max 69 if the producer/brand name does not appear in any web snippet

Respond in JSON only — no explanation, no markdown fences:
{{
  "country": "...",
  "region": "...",
  "grapes": ["...", "..."],
  "is_blend": true or false,
  "organic": true or false,
  "confidence": 0-100
}}"""

STRICT_SUFFIX = "\n\nReturn only raw JSON, no text before or after."
