"""Interactive Trump speech prediction and fact-check demo."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_delegation import Task
from agent_delegation.agents import TrumpSpeechFactCheckAgent


DEFAULT_TRANSCRIPT = Path(__file__).parent / "data" / "trump_sample_transcript.txt"


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Predict likely next words and flag claim-like statements."
    )
    parser.add_argument(
        "--transcript",
        default=str(DEFAULT_TRANSCRIPT),
        help="Path to transcript text file used to train the predictor.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="How many next-word predictions to display.",
    )
    args = parser.parse_args()

    transcript_text = Path(args.transcript).read_text(encoding="utf-8")
    agent = TrumpSpeechFactCheckAgent()

    train_task = Task(
        task_type="trump_speech_prediction",
        params={"operation": "train", "transcripts": [transcript_text]},
    )
    train_result = await agent.execute(train_task)
    print("Model trained:", train_result)
    print("Type partial lines. Enter 'quit' to stop.\n")

    while True:
        line = input("speech> ").strip()
        if line.lower() in {"quit", "exit"}:
            print("Goodbye.")
            return
        if not line:
            continue

        analysis_task = Task(
            task_type="trump_fact_check",
            params={
                "operation": "analyze_live_line",
                "prompt": line,
                "text": line,
                "top_k": args.top_k,
            },
        )
        result = await agent.execute(analysis_task)

        predictions = result["predictions"]["predictions"]
        if predictions:
            print("Predicted next words:")
            for idx, item in enumerate(predictions, start=1):
                print(f"  {idx}. {item['word']} ({item['probability']:.0%})")
        else:
            print("Predicted next words: no strong local match in the transcript.")

        checks = result["fact_check"]["checks"]
        if checks:
            print("Fact-check flags:")
            for item in checks:
                print(f"  - [{item['verdict']}] {item['claim']}")
                print(f"    {item['explanation']}")
                print(f"    Source: {item['source']}")
        else:
            print("Fact-check flags: none for this line.")
        print()


if __name__ == "__main__":
    asyncio.run(main())
