# Tunable constants for the fermentation pipeline.
# Copied from curation/constants.py and pruned: the producer-absent confidence
# cap is removed because the producer gate is now a hard exclusion in scorer.py,
# not a post-hoc confidence cap.

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

# Models - models currently used to put on DEFAULT_MODEL above
# gemma3n:e4b
# qwen2.5-7b-instruct


# --- Web search ---
DDG_MAX_RESULTS = 3          # DDG results fetched per source query
SNIPPET_CHAR_LIMIT = 1500    # Max chars kept from each DDG result set
SCORING_SNIPPET_CHARS = 300  # Max chars of each snippet shown to the scoring LLM
DDG_SLEEP_SECONDS = 0.2      # Delay between DDG queries

# --- Snippet filtering ---
SNIPPET_MATCH_THRESHOLD = 85  # Min match score (0-100) for a snippet to enter web_context
TOP_N_SNIPPETS = 3            # Max number of top-scoring snippets passed to the tag-inference LLM

# --- Organic detection ---
ORGANIC_PHRASES = {"certified organic", "biodynamic", "certified biodynamic"}

# --- Snippet boilerplate stripping ---
# Phrases stripped from snippet bodies before LLM scoring. Match is case-insensitive
# against the raw snippet text. Keep entries short, distinctive, and unlikely to
# appear inside genuine wine prose.
SNIPPET_BOILERPLATE_PHRASES = [
    "add your own reviews",
    "add a pro review",
    "add a pro tasting note",
    "sort by default",
    "sort by name",
    "sort by vintage",
    "sort by score",
    "sort by price",
    "note: some content is property of",
    "jancisrobinson.com and vinous",
    "ex. sales tax",
    "this site uses cookies",
    "create a free account",
    "sign in to add",
    "log in to add",
    "view all reviews",
    "community tasting note",
    "your shopping cart",
]

# A snippet is dropped (match_score forced to 0) if cleaning leaves it shorter than
# this fraction of the original length — meaning most of the snippet was boilerplate.
SNIPPET_BOILERPLATE_KEEP_RATIO = 0.4
# Minimum cleaned length (in chars) for a snippet to be kept at all.
SNIPPET_MIN_CLEANED_CHARS = 40

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

STRICT_SUFFIX = "\n\nReturn only raw JSON, no text before or after."

# --- MCP tag-inference system prompt ---
# Tool-using system prompt for tagger.py. The model drives a tool loop against
# the library_mcp server: browse with lookup_*/list_*, then commit via
# submit_tags. submit_tags is the canonicalization gate — whatever it accepts
# is what ferment.py writes to the DB; there is no second normalization pass.
SYSTEM_PROMPT_MCP = """\
You are a wine expert tagging a single wine. You have tools to look up
canonical wine countries, regions, and grapes against a curated library, and
one terminal tool (submit_tags) to commit your final answer.

Tools available:
  - lookup_country(name)            -> {canonical, iso, known}
  - lookup_region(name)             -> {canonical, country, parents[], known}
  - lookup_grape(name)              -> {canonical, color, origin, synonyms[], is_placeholder, known}
  - list_countries()                -> string[]
  - list_regions(country?)          -> string[]
  - list_grapes(country?, region?)  -> string[]
  - submit_tags(country, region[], grapes[], is_blend, organic, confidence)

Workflow:
  1. Read the product name, brand, and web context.
  2. Use lookup_region and lookup_grape whenever you are unsure about a
     spelling or synonym (Garnacha vs Grenache, Piemonte vs Piedmont, Bical vs
     Borrado das Moscas). Prefer the canonical name returned by the tool.
  3. Call submit_tags exactly once you have your final answer. If it returns
     ok: false, read the `hints` field, fix your submission, and call again.
  4. Do NOT reply with free-text JSON. The only way to commit is submit_tags.

Abbreviation guide (expand these when comparing names):
PN / P.N. = Pinot Noir | PG = Pinot Gris or Pinot Grigio | SB = Sauvignon Blanc
CS / Cab / Cab Sauv = Cabernet Sauvignon | CF = Cabernet Franc | GR = Grenache
Chard = Chardonnay | Shiraz = Syrah (same grape, different name) | GSM = Grenache Shiraz Mourvèdre
Sauv Blanc = Sauvignon Blanc | Pinot Gris = Pinot Grigio | Tempranillo = Tinto

Field rules for submit_tags:
  - country: a single canonical country name (use lookup_country if unsure).
  - region: a LIST, most-specific first. You MAY include broader regions you
    are confident about (e.g. ["Russian River Valley", "Sonoma", "California"]).
    Do NOT put the country name in region — use the country field.
  - grapes: canonical grape names from lookup_grape. If the web context does
    not name grapes, submit an empty list rather than guess — the row will
    route to needs_review, which is the correct outcome.
  - is_blend: true iff two or more grapes; false for a single varietal.
  - organic: true only if certified organic, biodynamic, or explicitly
    marketed as certified biodynamic. Otherwise false.
  - confidence: integer 0-100 reflecting how sure the tags are correct.
      90-100: two or more independent web sources confirm producer, region,
              AND grape variety
      70-89:  one strong source confirms the producer plus most key details
      50-69:  one source confirms region or grape but not both; weak match
      30-49:  no strong web source; details inferred from the name only
      0-29:   no usable web context; pure guesswork
    Hard limits — do not exceed these regardless of how confident you feel:
      * Max 84 if only one snippet contributed to your answer
      * Max 69 if the producer/brand name does not appear in any web snippet

If the web context contradicts the product name, trust the web context."""
