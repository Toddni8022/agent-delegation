"""Simple transcript fact-check runner.

Usage:
    python examples/fact_check_transcript.py --transcript path/to/speech.txt
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from agent_delegation import Task
from agent_delegation.agents import TrumpSpeechFactCheckAgent


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fact-check a full speech transcript from a text file."
    )
    parser.add_argument(
        "--transcript",
        required=True,
        help="Path to transcript text file.",
    )
    parser.add_argument(
        "--output",
        default="fact_check_report.json",
        help="Output JSON report path.",
    )
    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    agent = TrumpSpeechFactCheckAgent()
    result = await agent.execute(
        Task(
            task_type="trump_fact_check",
            params={
                "operation": "fact_check",
                "transcript_path": str(transcript_path),
            },
        )
    )

    output_path = Path(args.output)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Processed transcript: {transcript_path}")
    print(f"Checks found: {result['checks_count']}")
    print(f"Report saved to: {output_path.resolve()}")

    for item in result["checks"][:10]:
        print(f"- [{item['verdict']}] {item['claim']}")

    remaining = max(result["checks_count"] - 10, 0)
    if remaining:
        print(f"... and {remaining} more checks in the JSON report.")


if __name__ == "__main__":
    asyncio.run(main())
