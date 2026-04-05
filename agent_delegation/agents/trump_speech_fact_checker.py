"""Trump speech prediction and fact-checking agent."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..core.agent import Agent, AgentCapability
from ..core.task import Task


_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


class TrumpSpeechFactCheckAgent(Agent):
    """
    Agent that predicts likely next words and flags claims for fact-checking.

    Supported task types:
    - trump_speech_prediction
    - trump_fact_check
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "TrumpSpeechIntel",
        ngram_size: int = 3,
        fact_rules: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ):
        super().__init__(agent_id, name, **kwargs)
        if ngram_size < 2:
            raise ValueError("ngram_size must be at least 2")

        self.ngram_size = ngram_size
        self._prefix_counts: Dict[Tuple[str, ...], Counter[str]] = defaultdict(Counter)
        self._unigram_counts: Counter[str] = Counter()
        self._is_trained = False

        self._fact_rules = [
            {
                "pattern": r"\b(stolen|rigged)\s+election\b",
                "verdict": "unsupported",
                "explanation": (
                    "U.S. courts and state audits did not find evidence that "
                    "would change the 2020 election outcome."
                ),
                "source": "Multiple court rulings and state election audits (2020-2021)",
            },
            {
                "pattern": r"\blargest\s+inauguration\s+crowd\b",
                "verdict": "unsupported",
                "explanation": (
                    "Photographic evidence and transit data showed smaller attendance "
                    "than prior inaugurations."
                ),
                "source": "National Park Service images and transit metrics (2017)",
            },
            {
                "pattern": r"\b(mexico|mexican)\b.*\bpaid\b.*\bwall\b",
                "verdict": "unsupported",
                "explanation": "U.S. appropriations and reallocations funded border wall construction.",
                "source": "U.S. federal budget and appropriations records",
            },
        ]
        if fact_rules:
            self._fact_rules.extend(fact_rules)

        self.register_capabilities(
            [
                AgentCapability("trump_speech_prediction", version="1.0"),
                AgentCapability("trump_fact_check", version="1.0"),
            ]
        )

    async def execute(self, task: Task) -> Any:
        """Execute prediction or fact-check operations."""
        if task.task_type not in self.get_capabilities():
            raise ValueError(f"Agent cannot handle task type: {task.task_type}")

        operation = task.params.get("operation")
        if operation == "train":
            transcripts = self._load_transcripts(task.params)
            return self.train(transcripts)
        if operation == "predict_next_words":
            prompt = task.params.get("prompt", "")
            top_k = int(task.params.get("top_k", 5))
            return self.predict_next_words(prompt=prompt, top_k=top_k)
        if operation == "fact_check":
            text = self._load_fact_check_text(task.params)
            return self.fact_check_text(text=text)
        if operation == "analyze_live_line":
            prompt = task.params.get("prompt", "")
            text = task.params.get("text", prompt)
            top_k = int(task.params.get("top_k", 5))
            return {
                "predictions": self.predict_next_words(prompt=prompt, top_k=top_k),
                "fact_check": self.fact_check_text(text=text),
            }
        raise ValueError(f"Unknown operation: {operation}")

    def _load_fact_check_text(self, params: Dict[str, Any]) -> str:
        """Load fact-check text from inline fields and/or file paths."""
        text = params.get("text")
        if isinstance(text, str) and text.strip():
            return text

        combined_texts: List[str] = []
        raw_texts = params.get("texts", [])
        if isinstance(raw_texts, list):
            combined_texts.extend(str(item) for item in raw_texts if str(item).strip())

        transcript_path = params.get("transcript_path")
        if transcript_path:
            combined_texts.append(Path(transcript_path).read_text(encoding="utf-8"))

        transcript_paths = params.get("transcript_paths", [])
        if isinstance(transcript_paths, list):
            for raw_path in transcript_paths:
                combined_texts.append(Path(raw_path).read_text(encoding="utf-8"))

        joined_text = "\n".join(segment for segment in combined_texts if segment.strip()).strip()
        if joined_text:
            return joined_text
        raise ValueError("No text provided for fact-checking")

    def _load_transcripts(self, params: Dict[str, Any]) -> List[str]:
        """Load transcript input from inline text and/or file paths."""
        transcripts: List[str] = []

        inline_transcripts = params.get("transcripts", [])
        if isinstance(inline_transcripts, str):
            transcripts.append(inline_transcripts)
        elif isinstance(inline_transcripts, list):
            transcripts.extend(str(item) for item in inline_transcripts)

        transcript_path = params.get("transcript_path")
        if transcript_path:
            file_text = Path(transcript_path).read_text(encoding="utf-8")
            transcripts.append(file_text)

        transcript_paths = params.get("transcript_paths", [])
        if isinstance(transcript_paths, list):
            for raw_path in transcript_paths:
                file_text = Path(raw_path).read_text(encoding="utf-8")
                transcripts.append(file_text)

        if not transcripts:
            raise ValueError("No training transcripts provided")
        return transcripts

    def _tokenize(self, text: str) -> List[str]:
        return [token.lower() for token in _TOKEN_RE.findall(text)]

    def train(self, transcripts: Iterable[str]) -> Dict[str, Any]:
        """Train n-gram model on transcript texts."""
        self._prefix_counts.clear()
        self._unigram_counts.clear()

        total_tokens = 0
        transcript_count = 0
        start_tokens = ["<s>"] * (self.ngram_size - 1)

        for text in transcripts:
            transcript_count += 1
            tokens = self._tokenize(text)
            if not tokens:
                continue
            total_tokens += len(tokens)
            self._unigram_counts.update(tokens)

            framed = start_tokens + tokens + ["</s>"]
            for index in range(len(framed) - self.ngram_size + 1):
                prefix = tuple(framed[index : index + self.ngram_size - 1])
                next_token = framed[index + self.ngram_size - 1]
                self._prefix_counts[prefix][next_token] += 1

        if total_tokens == 0:
            raise ValueError("Training transcripts do not contain usable words")

        self._is_trained = True
        return {
            "trained": True,
            "transcript_count": transcript_count,
            "total_tokens": total_tokens,
            "vocabulary_size": len(self._unigram_counts),
            "ngram_size": self.ngram_size,
        }

    def _best_prefix_for_prompt(self, prompt_tokens: List[str]) -> Optional[Tuple[str, ...]]:
        max_len = self.ngram_size - 1
        for size in range(max_len, 0, -1):
            partial = prompt_tokens[-size:] if prompt_tokens else []
            prefix = tuple((["<s>"] * (max_len - size)) + partial)
            if prefix in self._prefix_counts:
                return prefix
        cold_start = tuple(["<s>"] * max_len)
        if cold_start in self._prefix_counts:
            return cold_start
        return None

    def predict_next_words(self, prompt: str, top_k: int = 5) -> Dict[str, Any]:
        """Return top-k next-token predictions for a prompt."""
        if not self._is_trained:
            raise ValueError("Model has not been trained yet")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        prompt_tokens = self._tokenize(prompt)
        prefix = self._best_prefix_for_prompt(prompt_tokens)
        if not prefix:
            return {"prompt": prompt, "predictions": [], "model_ready": True}

        next_counts = self._prefix_counts[prefix]
        total = sum(next_counts.values()) or 1
        ranked = next_counts.most_common(top_k)

        return {
            "prompt": prompt,
            "context_tokens": list(prefix),
            "predictions": [
                {
                    "word": token,
                    "count": count,
                    "probability": round(count / total, 4),
                }
                for token, count in ranked
                if token != "</s>"
            ],
            "model_ready": True,
        }

    def fact_check_text(self, text: str) -> Dict[str, Any]:
        """Flag claim-like sentence fragments and apply rule-based checks."""
        sentences = [segment.strip() for segment in re.split(r"[.!?]+", text) if segment.strip()]
        checks: List[Dict[str, str]] = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            matched = False
            for rule in self._fact_rules:
                if re.search(rule["pattern"], sentence_lower):
                    checks.append(
                        {
                            "claim": sentence,
                            "verdict": rule["verdict"],
                            "explanation": rule["explanation"],
                            "source": rule["source"],
                        }
                    )
                    matched = True
                    break

            if not matched and self._is_claim_like(sentence_lower):
                checks.append(
                    {
                        "claim": sentence,
                        "verdict": "needs_review",
                        "explanation": (
                            "This looks like a factual claim. No local match was found, "
                            "so verify it with a trusted source."
                        ),
                        "source": "Manual verification required",
                    }
                )

        return {"text": text, "checks": checks, "checks_count": len(checks)}

    def _is_claim_like(self, sentence: str) -> bool:
        """Simple heuristic for identifying factual claims."""
        has_digit = any(char.isdigit() for char in sentence)
        claim_keywords = (
            "is",
            "are",
            "was",
            "were",
            "will",
            "won",
            "largest",
            "biggest",
            "percent",
            "million",
            "billion",
            "first",
            "never",
            "always",
        )
        return has_digit or any(keyword in sentence for keyword in claim_keywords)
