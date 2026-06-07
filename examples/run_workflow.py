#!/usr/bin/env python3
"""Example: Execute a multi-agent workflow via the platform API."""

import asyncio
import json
import sys

import httpx


async def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    query = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "How should we design an enterprise multi-agent AI platform?"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Query: {query}\n")

        cost_estimate = await client.post(
            f"{base_url}/api/v1/workflow/estimate-cost",
            json={"query": query},
        )
        print("Cost Estimate:")
        print(json.dumps(cost_estimate.json(), indent=2))
        print()

        response = await client.post(
            f"{base_url}/api/v1/workflow/execute",
            json={"query": query},
        )
        result = response.json()

        if result.get("result"):
            r = result["result"]
            print(f"Status: {r['status']}")
            print(f"Request ID: {r['request_id']}")
            print(f"Tokens: {r['total_tokens']} | Cost: ${r['total_cost_usd']:.4f}")
            print(f"Latency: {r['total_latency_ms']:.0f}ms\n")

            summary = r.get("executive_summary", {})
            print(f"Headline: {summary.get('headline', 'N/A')}")
            print("\nKey Insights:")
            for insight in summary.get("key_insights", []):
                print(f"  • {insight}")

            print("\nAction Items:")
            for item in summary.get("action_items", []):
                print(f"  • [{item.get('priority', 'medium')}] {item['description']}")

        eval_response = await client.post(
            f"{base_url}/api/v1/workflow/evaluate",
            json={"query": query},
        )
        if eval_response.status_code == 200:
            scorecard = eval_response.json()
            print("\nEvaluation Scorecard:")
            print(f"  Task Completion:    {scorecard['task_completion']:.2f}")
            print(f"  Groundedness:       {scorecard['groundedness']:.2f}")
            print(f"  Hallucination Rate: {scorecard['hallucination_rate']:.2f}")
            print(f"  Agent Accuracy:     {scorecard['agent_accuracy']:.2f}")
            print(f"  Cost Efficiency:    {scorecard['cost_efficiency']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
