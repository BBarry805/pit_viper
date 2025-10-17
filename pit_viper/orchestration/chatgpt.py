"""Wrapper around the OpenAI API for ChatGPT-5 advice generation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AdviceRequest:
    market_overview: Dict[str, Any]
    recommendations: Dict[str, Any]
    portfolio: Dict[str, Any]
    sentiment: Dict[str, Any]


class ChatGPTClient:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def generate_advice(self, request: AdviceRequest) -> Dict[str, Any]:
        """Call the OpenAI API or provide a deterministic mock if unavailable."""
        payload = {
            "market_overview": request.market_overview,
            "recommendations": request.recommendations,
            "portfolio": request.portfolio,
            "sentiment": request.sentiment,
        }
        if not self.api_key:
            return {
                "summary": "Mock advice: diversify across highlighted assets and review risk limits.",
                "details": payload,
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            completion = client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": "You are a registered investment adviser assistant. Provide balanced daily insights including rationale and risks.",
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload, default=str),
                    },
                ],
                max_output_tokens=800,
                temperature=0.3,
            )
            message = completion.output[0].content[0].text
            return {"summary": message, "details": payload}
        except Exception:
            return {
                "summary": "Mock advice (API error): review highlighted assets, maintain discipline on position sizing.",
                "details": payload,
            }


__all__ = ["AdviceRequest", "ChatGPTClient"]
