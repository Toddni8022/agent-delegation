"""Tests for TrumpSpeechFactCheckAgent."""

import pytest

from agent_delegation.agents import TrumpSpeechFactCheckAgent
from agent_delegation.core.task import Task


@pytest.mark.asyncio
async def test_agent_capabilities():
    """Agent exposes prediction and fact-check capabilities."""
    agent = TrumpSpeechFactCheckAgent()
    assert agent.has_capability("trump_speech_prediction")
    assert agent.has_capability("trump_fact_check")


@pytest.mark.asyncio
async def test_predict_next_words_after_training():
    """Train model and return ranked next-word predictions."""
    agent = TrumpSpeechFactCheckAgent()
    train_task = Task(
        task_type="trump_speech_prediction",
        params={
            "operation": "train",
            "transcripts": [
                "We will win big and we will win now.",
                "We will win big league.",
            ],
        },
    )
    await agent.execute(train_task)

    predict_task = Task(
        task_type="trump_speech_prediction",
        params={"operation": "predict_next_words", "prompt": "we will", "top_k": 3},
    )
    result = await agent.execute(predict_task)

    assert result["model_ready"] is True
    assert len(result["predictions"]) >= 1
    assert result["predictions"][0]["word"] == "win"


@pytest.mark.asyncio
async def test_predict_without_training_raises():
    """Predicting before training should fail."""
    agent = TrumpSpeechFactCheckAgent()
    predict_task = Task(
        task_type="trump_speech_prediction",
        params={"operation": "predict_next_words", "prompt": "we will"},
    )
    with pytest.raises(ValueError):
        await agent.execute(predict_task)


@pytest.mark.asyncio
async def test_fact_check_known_claim():
    """Known claims should map to local fact rules."""
    agent = TrumpSpeechFactCheckAgent()
    check_task = Task(
        task_type="trump_fact_check",
        params={
            "operation": "fact_check",
            "text": "The largest inauguration crowd ever was at my inauguration.",
        },
    )
    result = await agent.execute(check_task)

    assert result["checks_count"] == 1
    assert result["checks"][0]["verdict"] == "unsupported"


@pytest.mark.asyncio
async def test_analyze_live_line_combines_outputs():
    """Live analysis should include both predictions and fact checks."""
    agent = TrumpSpeechFactCheckAgent()
    await agent.execute(
        Task(
            task_type="trump_speech_prediction",
            params={
                "operation": "train",
                "transcripts": ["America is strong and America is winning."],
            },
        )
    )

    result = await agent.execute(
        Task(
            task_type="trump_fact_check",
            params={
                "operation": "analyze_live_line",
                "prompt": "america is",
                "text": "America is winning.",
                "top_k": 2,
            },
        )
    )

    assert "predictions" in result
    assert "fact_check" in result
    assert isinstance(result["predictions"]["predictions"], list)
    assert isinstance(result["fact_check"]["checks"], list)


@pytest.mark.asyncio
async def test_fact_check_from_transcript_path(tmp_path):
    """Fact-check operation can read transcript text from file path."""
    transcript = tmp_path / "speech.txt"
    transcript.write_text(
        "The election was stolen. "
        "Mexico paid for the wall. "
        "We had 10 million people at a rally.",
        encoding="utf-8",
    )

    agent = TrumpSpeechFactCheckAgent()
    result = await agent.execute(
        Task(
            task_type="trump_fact_check",
            params={"operation": "fact_check", "transcript_path": str(transcript)},
        )
    )

    assert result["checks_count"] == 3
    verdicts = [item["verdict"] for item in result["checks"]]
    assert "unsupported" in verdicts
    assert "needs_review" in verdicts
