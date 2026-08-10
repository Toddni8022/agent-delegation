"""Example agent implementations."""

from .data_processor import DataProcessingAgent
from .api_caller import APICallAgent
from .trump_speech_fact_checker import TrumpSpeechFactCheckAgent

__all__ = [
    'DataProcessingAgent',
    'APICallAgent',
    'TrumpSpeechFactCheckAgent',
]
