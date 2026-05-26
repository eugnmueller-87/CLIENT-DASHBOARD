"""
LLM token instrumentation — drop this file into any Python client project.

Usage
-----
1. pip install prometheus-client anthropic openai mistralai

2. Set the CLIENT_NAME env var to match the project slug used in Grafana
   (e.g. "metabelly", "client-b"). This is how tokens land under the right
   client in the dashboard.

3. Call track_anthropic / track_openai / track_mistral after each API call,
   or use the decorator versions.

4. Mount the /metrics endpoint (see bottom of file for FastAPI + Flask examples).
"""

import os
import functools
from prometheus_client import Counter, start_http_server, make_asgi_app

# ── The client label — set CLIENT_NAME in the app's environment ──────────────
CLIENT = os.environ.get("CLIENT_NAME", "unknown")

TOKENS = Counter(
    "api_tokens_used_total",
    "LLM API token consumption",
    ["client", "provider", "token_type", "model"],
)


def _inc(provider: str, model: str, input_tokens: int, output_tokens: int) -> None:
    TOKENS.labels(client=CLIENT, provider=provider, token_type="input",  model=model).inc(input_tokens)
    TOKENS.labels(client=CLIENT, provider=provider, token_type="output", model=model).inc(output_tokens)


# ── Anthropic ─────────────────────────────────────────────────────────────────

def track_anthropic(response) -> None:
    """Call after anthropic_client.messages.create(). Passes the response through."""
    _inc(
        provider="anthropic",
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return response


def anthropic_create(client, **kwargs):
    """Drop-in wrapper for client.messages.create(**kwargs)."""
    response = client.messages.create(**kwargs)
    track_anthropic(response)
    return response


# ── OpenAI ────────────────────────────────────────────────────────────────────

def track_openai(response) -> None:
    """Call after openai_client.chat.completions.create(). Passes the response through."""
    _inc(
        provider="openai-mini" if "mini" in response.model else "openai",
        model=response.model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )
    return response


def openai_create(client, **kwargs):
    """Drop-in wrapper for client.chat.completions.create(**kwargs)."""
    response = client.chat.completions.create(**kwargs)
    track_openai(response)
    return response


# ── Mistral ───────────────────────────────────────────────────────────────────

def track_mistral(response) -> None:
    """Call after mistral_client.chat.complete(). Passes the response through."""
    model = response.model or "mistral"
    provider = "mistral-small" if any(x in model for x in ("small", "nemo", "7b")) else "mistral"
    _inc(
        provider=provider,
        model=model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )
    return response


def mistral_complete(client, **kwargs):
    """Drop-in wrapper for client.chat.complete(**kwargs)."""
    response = client.chat.complete(**kwargs)
    track_mistral(response)
    return response


# ── Mounting /metrics ─────────────────────────────────────────────────────────

def get_fastapi_metrics_app():
    """
    Mount on a FastAPI app:

        from llm_metrics import get_fastapi_metrics_app
        app.mount("/metrics", get_fastapi_metrics_app())
    """
    return make_asgi_app()


def start_standalone_metrics_server(port: int = 8000) -> None:
    """
    For non-ASGI apps (plain scripts, workers):

        from llm_metrics import start_standalone_metrics_server
        start_standalone_metrics_server(port=8000)

    Grafana Agent will scrape http://localhost:8000/metrics.
    """
    start_http_server(port)


# ── Flask example (commented out — uncomment if using Flask) ──────────────────
#
# from flask import Flask, Response
# from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
#
# def register_flask_metrics(app: Flask) -> None:
#     @app.route("/metrics")
#     def metrics():
#         return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
