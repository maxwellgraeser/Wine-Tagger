# Tunable constants for the fermentation pipeline.
# There is no producer-absent confidence cap: the producer gate is a hard
# exclusion in scorer.py, not a post-hoc confidence cap.

# --- Web search plan ---
# One DDG query per entry, per wine. `scope` is the site: domain the results
# must come from ("*" = unscoped; only ad-redirect hosts are filtered).
# Placeholders: {name} product name, {sku} barcode (entry skipped if the SKU is
# not 8-14 digits), {dist} the distributor's domain (entry skipped if the
# supplier is not in DISTRIBUTOR_SITES).
#
# Chosen from a 2026-09-15 experiment (11 wines x 15 templates, see
# fermentation/ACCURACY-2026-09-15.md): question-style unscoped queries found
# the TRUE grape for 11/11 wines with 97% of results passing the producer gate;
# the old '"{name}" wine region grapes' fallback managed 9/11; per-source UPC
# queries (site:cellartracker.com "{sku}") passed the gate only 37% of the time;
# totalwine.com timed out on 6/11. Every query costs ~1 s and engines throttle
# bursts, so the plan is 9 queries per wine, down from 12.
SEARCH_QUERIES = [
    # label,                    template,                                  scope
    ("Grapes Q",                "what grapes are in {name} wine",          "*"),
    ("Region Q",                "what region is {name} wine made in",      "*"),
    ("Wine Searcher",           'site:wine-searcher.com "{name}"',         "wine-searcher.com"),
    ("Vivino",                  'site:vivino.com "{name}"',                "vivino.com"),
    ("CellarTracker",           'site:cellartracker.com "{name}"',         "cellartracker.com"),
    ("Wine.com",                'site:wine.com "{name}"',                  "wine.com"),
    ("UPC",                     '"{sku}" wine',                            "*"),
    ("{supplier} (distributor)", "site:{dist} {name}",                     "{dist}"),
    ("fallback",                "{name} wine",                             "*"),
]

# Distributor / importer websites, keyed by a lowercase substring of the
# Lightspeed `supplier_name`. Importer pages, when the engine has indexed
# them, list the exact blend and appellation of the wine actually shipped —
# but indexing is thin (5/11 wines in the experiment). Add a line per
# supplier you buy from.
DISTRIBUTOR_SITES = {
    "winebow":          "winebow.com",
    "monsieur touton":  "monsieurtouton.com",
}

# --- LLM / API ---
DEFAULT_API_URL = "http://localhost:8080/v1/chat/completions"
DEFAULT_MODEL = "qwen2.5-7b-instruct"
DEFAULT_CONFIDENCE_THRESHOLD = 85   # initial value; settings.json (see settings.py) overrides it

# Models - models previously used for DEFAULT_MODEL above
# qwen2.5-7b-instruct  -- current default; gemma3n has no working tool-call
#                         support in llama.cpp (its chat template ignores
#                         `tools`, and its native tool_code/tool_output
#                         convention isn't parsed by tagger.py or llama-server's
#                         generic tool-call handling)
# gemma3n:e4b


# --- Web search ---
DDG_MAX_RESULTS = 3          # DDG results fetched per source query
SNIPPET_CHAR_LIMIT = 2000    # Max chars kept from each DDG result (p90 of real snippets is ~1400)
SCORING_SNIPPET_CHARS = 600  # Max chars of each snippet shown to the scoring LLM
                             # (was 300 — the producer name is often past that point)
SCORING_TIMEOUT_SECONDS = 120  # One scoring call: ~25 snippets x 600 chars is ~4k tokens of
                               # prompt, ~40 s on a 7B model; 45 s timed out under load
DDG_SLEEP_SECONDS = 0.2      # Stagger between DDG query starts
DDG_CONCURRENCY = 4          # DDG queries run in parallel per wine (1 = sequential)
DDG_TIMEOUT_SECONDS = 10     # Per-engine wait inside ddgs (5 s timed out 7 of 11 queries on a busy run)
DDG_BACKEND = "yahoo,bing,duckduckgo"
# ddgs tries these engines in THIS order, one at a time (with max_results<=10 it
# only runs one engine per attempt), moving on when one errors. "auto" shuffles
# the order and usually lands on html.duckduckgo.com first, which on 2026-09-15
# timed out on ~70% of queries; yahoo answered the same site: queries in <1 s.
# Bing ignores site: for its ad slots, so site-scoped results are also filtered
# by URL host (see searcher._on_site).
DDG_RETRY_DELAYS = (15, 45)  # If a wine gets ZERO results from every query (rate limit),
                             # wait this many seconds and retry the whole plan, once per entry

# --- Snippet filtering ---
SNIPPET_DEDUPE_JACCARD = 0.9  # Two snippets whose word sets overlap this much (Jaccard, words of
                              # 3+ letters, digits ignored so vintages don't matter) are near-
                              # duplicates — e.g. one price page returned for three vintages. Only
                              # the first is kept. 0.9 collapsed 53 of 340 snippets on the 24-wine
                              # test run; 0.8 starts merging different pages that share boilerplate.
SNIPPET_MATCH_THRESHOLD = 85  # Min match score (0-100) for a snippet to enter web_context
TOP_N_SNIPPETS = 5            # Max number of top-scoring snippets passed to the tag-inference LLM.
                              # Picked for source diversity: the distributor's snippet (if any) first,
                              # then the best snippet from each distinct source, then by score.
                              # Since tagging moved to the MCP tool loop the prompt no longer carries
                              # reference tables, so there is room for 5 x SNIPPET_CHAR_LIMIT
                              # (~2.5k tokens) — and the confidence rubric wants >= 2 sources.

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

Product names may abbreviate the grape (PN = Pinot Noir, SB = Sauvignon Blanc,
Cab = Cabernet Sauvignon); treat such abbreviations as the full name when comparing.

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
  - lookup_region(name)             -> {canonical, country, parents[], classification, is_placeholder, known}
  - lookup_grape(name)              -> {canonical, color, origin, synonyms[], is_phrase, is_placeholder, known}
  - list_countries()                -> string[]
  - list_regions(country?)          -> string[]
  - list_grapes(country?, region?)  -> string[]
  - submit_tags(country, region[], grapes[], is_blend, organic, confidence)

The library has two tiers. Canonical entries are what submit_tags accepts
and what list_* return. Placeholder entries (is_placeholder: true) are real
but niche regions/grapes; submit_tags rejects them -- for a placeholder
region use the nearest canonical name from its `parents`, for a placeholder
grape use the common name the source uses, or drop it.

Workflow:
  1. Read the product name, brand, and web context.
  2. Use lookup_region and lookup_grape whenever you are unsure about a
     spelling or synonym (Garnacha vs Grenache, Piemonte vs Piedmont, Bical vs
     Borrado das Moscas). Prefer the canonical name returned by the tool.
  3. Call submit_tags once you have your final answer. If it returns
     ok: false, read the `hints` field (it names the offending values), fix
     your submission, and call again. Unknown names never pass: fix the
     spelling via lookup_*, or drop the value and keep what you are sure of.
  4. Do NOT reply with free-text JSON. The only way to commit is submit_tags.

Field rules for submit_tags:
  - country: a single canonical country name (use lookup_country if unsure).
  - region: a LIST, most-specific first. Parent regions are added for you
    (["Russian River Valley"] becomes [Russian River Valley, Sonoma County,
    North Coast, California]), so submit the most specific canonical region
    you can support. Do NOT put the country name in region — use the
    country field.
  - grapes: canonical grape names from lookup_grape, and ONLY grapes that a
    web snippet actually names for this wine. Never infer a grape from the
    region, the style, or a word in the product name ("Tinto", "Rosé",
    "Old Vines" are not grapes). If no snippet names the grapes, submit an
    empty list — it is accepted and the row routes to needs_review, which
    is the correct outcome. lookup_grape resolves abbreviations and synonyms
    (PN, Shiraz, Garnacha, Tinta Roriz), so look them up instead of guessing.
  - is_blend: true if two or more grapes, OR if a snippet calls the wine a
    blend ("Tempranillo Blend", "Red Rhône Blend") even when only one grape
    is named; false for a confirmed single varietal.
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
