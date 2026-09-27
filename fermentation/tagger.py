"""LLM tag inference via the library_mcp tool loop.

Owns:
    * Spawning the library_mcp stdio subprocess (once per ferment.py run)
    * Driving the llama.cpp tool-call loop against /v1/chat/completions
    * Routing tool_calls to the MCP server and feeding results back
    * Extracting the canonical `normalized` block from submit_tags

Does not own: snippet prep, scoring, DB writes.
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from typing import Any, Optional

import requests

from .constants import SYSTEM_PROMPT_MCP
from .types import ParsedTags, Product

# --- Tool-call loop budget -------------------------------------------------

MAX_ITERS = 8
MAX_SUBMIT_RETRIES = 3
HTTP_TIMEOUT_SECONDS = 120


# --- Tool schema advertised to the model ----------------------------------
# Built from the server's own `list_tools()` at session start, so the model
# always sees exactly the surface library_mcp/server.py exposes.

def _strip_titles(schema: Any) -> Any:
    """Drop pydantic's auto-generated `title` keys -- prompt noise for the model."""
    if isinstance(schema, dict):
        return {k: _strip_titles(v) for k, v in schema.items() if k != "title"}
    if isinstance(schema, list):
        return [_strip_titles(v) for v in schema]
    return schema


def _to_openai_tool(tool: Any) -> dict[str, Any]:
    """Convert an `mcp.types.Tool` to the OpenAI function-tool shape llama.cpp expects."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            # Collapse docstring indentation/newlines -- tokens, not meaning.
            "description": " ".join((tool.description or "").split()),
            "parameters": _strip_titles(tool.inputSchema),
        },
    }


# --- Sync wrapper around the async MCP client ------------------------------

class _SyncMCPSession:
    """Synchronous facade for `mcp.ClientSession`.

    The MCP Python SDK is async-only, but the rest of fermentation is sync.
    We run a private event loop on a background thread and proxy each
    `call_tool` through it. The loop and the stdio subprocess live for the
    entire `library_mcp_session()` context — one spawn per ferment.py run.
    """

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._session = None
        self._enter_exc: Optional[BaseException] = None
        self._stack = None  # contextlib.AsyncExitStack, populated in _run
        self.tools: list[dict[str, Any]] = []  # OpenAI-shaped, from list_tools()

    def __enter__(self) -> "_SyncMCPSession":
        self._thread = threading.Thread(target=self._run, name="mcp-session", daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._enter_exc is not None:
            raise self._enter_exc
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Signal the loop thread to tear down and wait for it.
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._stop.set)
            # Schedule a wake-up future so the loop sees the stop flag.
            try:
                fut = asyncio.run_coroutine_threadsafe(self._wake(), self._loop)
                fut.result(timeout=10)
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=10)

    async def _wake(self) -> None:
        # No-op: just gives the event loop something to schedule so the
        # `while not stop` check below runs again.
        return None

    def _run(self) -> None:
        # Event loop thread: open the stdio session, hold it open, then close.
        from contextlib import AsyncExitStack

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def main() -> None:
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "fermentation.library_mcp.server"],
            )
            async with AsyncExitStack() as stack:
                try:
                    read, write = await stack.enter_async_context(stdio_client(params))
                    session = await stack.enter_async_context(ClientSession(read, write))
                    await session.initialize()
                    listed = await session.list_tools()
                    self.tools = [_to_openai_tool(t) for t in listed.tools]
                    self._session = session
                except BaseException as exc:  # noqa: BLE001
                    self._enter_exc = exc
                    self._ready.set()
                    return
                self._ready.set()
                # Idle until __exit__ flips the stop flag.
                while not self._stop.is_set():
                    await asyncio.sleep(0.05)

        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(main())
        finally:
            if self._loop is not None:
                try:
                    self._loop.close()
                except Exception:
                    pass

    def call_tool(self, name: str, args: dict[str, Any]) -> Any:
        """Synchronously dispatch a tool call to the MCP server.

        Returns the parsed JSON payload that the tool returned (FastMCP
        wraps dict returns as `structuredContent` plus a text mirror).
        """
        if self._loop is None or self._session is None:
            raise RuntimeError("MCP session not initialised")

        async def _call():
            return await self._session.call_tool(name, args or {})

        fut = asyncio.run_coroutine_threadsafe(_call(), self._loop)
        result = fut.result(timeout=HTTP_TIMEOUT_SECONDS)
        return _unwrap_call_tool_result(result)


def _unwrap_call_tool_result(result: Any) -> Any:
    """Extract the payload from an `mcp.types.CallToolResult`.

    FastMCP returns dicts as both `structuredContent` (already JSON) and a
    text content block (JSON-encoded). Prefer structuredContent; fall back
    to parsing the first text block; finally surface the raw text.
    """
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        # FastMCP sometimes wraps scalars/lists under a "result" key.
        if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
            return structured["result"]
        return structured

    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if text is None:
            continue
        try:
            return json.loads(text)
        except (TypeError, ValueError):
            return text
    return None


@contextmanager
def library_mcp_session():
    """Spawn the library_mcp stdio server for the duration of a run.

    Yields a session object with a synchronous `.call_tool(name, args)`
    method and `.tools`, the server's tool list in OpenAI function shape. Lifecycle is ONCE per ferment.py run, not per product.
    """
    session = _SyncMCPSession()
    session.__enter__()
    try:
        yield session
    finally:
        session.__exit__(None, None, None)


# --- LLM HTTP plumbing ----------------------------------------------------

def _post_llama(api_url: str, model: str, messages: list[dict], tools: list[dict]) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.0,
    }
    resp = requests.post(api_url, json=payload, timeout=HTTP_TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def _product_user_prompt(product: Product, web_context: str) -> str:
    return (
        "Tag this wine.\n\n"
        f"Product name: {product.name}\n"
        f"Brand: {product.brand or '(unknown)'}\n"
        f"SKU: {product.sku or '(none)'}\n"
        f"Category: {product.category or '(unknown) -- infer it: Red, White, Rose or Sparkling'}\n"
        f"Supplier: {product.supplier or '(unknown)'}\n\n"
        "Web context (top scored snippets, most relevant first):\n"
        "---\n"
        f"{web_context}\n"
        "---\n\n"
        "Use lookup_region / lookup_grape on anything you are unsure of, then "
        "call submit_tags. If submit_tags returns ok: false, read hints, fix "
        "your submission, and call again."
    )


def _parse_tool_args(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _to_parsed_tags(normalized: dict) -> ParsedTags:
    return ParsedTags(
        country=normalized.get("country"),
        region=list(normalized.get("region") or []),
        grapes=list(normalized.get("grapes") or []),
        is_blend=normalized.get("is_blend"),
        organic=normalized.get("organic"),
        confidence=normalized.get("confidence"),
        category=normalized.get("category"),
    )


def _json_dumps(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(str(value))


# --- Public entry point ---------------------------------------------------

def infer_tags(
    product: Product,
    web_context: str,
    *,
    api_url: str,
    model: str,
    mcp_session,
) -> tuple[Optional[ParsedTags], list[dict]]:
    """Drive the MCP tool-call loop for a single product.

    Returns ``(parsed_or_None, transcript)``. ``None`` means the model never
    produced a successful ``submit_tags`` within ``MAX_SUBMIT_RETRIES`` (or
    emitted free-text instead of a tool call). Caller writes the resulting
    product as ``tag_status='needs_review'``.
    """
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT_MCP},
        {"role": "user", "content": _product_user_prompt(product, web_context)},
    ]

    last_ok_normalized: Optional[dict] = None
    submit_failures = 0

    for _ in range(MAX_ITERS):
        resp = _post_llama(api_url, model, messages, mcp_session.tools)
        try:
            msg = resp["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            break

        # Persist the assistant turn verbatim so subsequent tool messages
        # reference its tool_call ids.
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": msg.get("content"),
        }
        tool_calls = msg.get("tool_calls") or []
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            # Model emitted free-text instead of a tool call. Loop ends.
            break

        for call in tool_calls:
            fn = (call.get("function") or {})
            name = fn.get("name") or ""
            args = _parse_tool_args(fn.get("arguments"))
            call_id = call.get("id") or ""

            try:
                result = mcp_session.call_tool(name, args)
            except Exception as exc:  # noqa: BLE001 — surface to model as tool error
                result = {"error": f"tool_dispatch_failed: {type(exc).__name__}: {exc}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": _json_dumps(result),
                }
            )

            if name == "submit_tags":
                if isinstance(result, dict) and result.get("ok"):
                    last_ok_normalized = result.get("normalized") or {}
                else:
                    submit_failures += 1
                    if submit_failures >= MAX_SUBMIT_RETRIES:
                        return None, messages

        if last_ok_normalized is not None:
            break

    if last_ok_normalized is None:
        return None, messages
    return _to_parsed_tags(last_ok_normalized), messages
