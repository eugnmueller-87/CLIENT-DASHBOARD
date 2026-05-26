/**
 * LLM token instrumentation — drop this file into any Node.js/TypeScript client project.
 *
 * Setup
 * -----
 * npm install prom-client
 *
 * Set CLIENT_NAME env var to the project slug used in Grafana
 * (e.g. "metabelly", "client-b"). This is how tokens land under the
 * right client in the dashboard.
 *
 * Mount the /metrics route (examples at bottom of file).
 */

import { Counter, Registry, collectDefaultMetrics } from "prom-client";

const CLIENT = process.env.CLIENT_NAME ?? "unknown";

export const registry = new Registry();
collectDefaultMetrics({ register: registry });

const tokens = new Counter({
  name: "api_tokens_used_total",
  help: "LLM API token consumption",
  labelNames: ["client", "provider", "token_type", "model"] as const,
  registers: [registry],
});

function inc(provider: string, model: string, inputTokens: number, outputTokens: number) {
  tokens.labels({ client: CLIENT, provider, token_type: "input",  model }).inc(inputTokens);
  tokens.labels({ client: CLIENT, provider, token_type: "output", model }).inc(outputTokens);
}

// ── Anthropic ──────────────────────────────────────────────────────────────

/** Pass the raw response from anthropic.messages.create() */
export function trackAnthropic<T extends { model: string; usage: { input_tokens: number; output_tokens: number } }>(
  response: T
): T {
  inc("anthropic", response.model, response.usage.input_tokens, response.usage.output_tokens);
  return response;
}

// ── OpenAI ────────────────────────────────────────────────────────────────

/** Pass the raw response from openai.chat.completions.create() */
export function trackOpenAI<T extends { model: string; usage?: { prompt_tokens: number; completion_tokens: number } | null }>(
  response: T
): T {
  if (response.usage) {
    const provider = response.model.includes("mini") ? "openai-mini" : "openai";
    inc(provider, response.model, response.usage.prompt_tokens, response.usage.completion_tokens);
  }
  return response;
}

// ── Mistral ───────────────────────────────────────────────────────────────

/** Pass the raw response from mistral.chat.complete() */
export function trackMistral<T extends { model?: string | null; usage?: { promptTokens: number; completionTokens: number } | null }>(
  response: T
): T {
  if (response.usage) {
    const model = response.model ?? "mistral";
    const provider = /small|nemo|7b/i.test(model) ? "mistral-small" : "mistral";
    inc(provider, model, response.usage.promptTokens, response.usage.completionTokens);
  }
  return response;
}

// ── Mounting /metrics ──────────────────────────────────────────────────────

/**
 * Express / Next.js API route handler.
 *
 * Express:
 *   import { metricsHandler } from "./llmMetrics";
 *   app.get("/metrics", metricsHandler);
 *
 * Next.js app/api/metrics/route.ts:
 *   import { metricsHandler } from "@/lib/llmMetrics";
 *   export { metricsHandler as GET };
 */
export async function metricsHandler(
  _req: unknown,
  res: { setHeader: (k: string, v: string) => void; end: (body: string) => void }
) {
  res.setHeader("Content-Type", registry.contentType);
  res.end(await registry.metrics());
}

/**
 * Next.js App Router — use this as the GET export in app/api/metrics/route.ts:
 *
 *   import { nextMetricsRoute } from "@/lib/llmMetrics";
 *   export const GET = nextMetricsRoute;
 */
export async function nextMetricsRoute() {
  const { NextResponse } = await import("next/server");
  const body = await registry.metrics();
  return new NextResponse(body, {
    headers: { "Content-Type": registry.contentType },
  });
}
