"""
LLM Service - Abstraction layer for LLM providers.

Supports Anthropic (default), OpenAI, and Ollama.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import yaml


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    usage: Optional[dict] = None


class LLMService(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response from the LLM."""
        pass


class AnthropicService(LLMService):
    """Anthropic Claude API wrapper."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", 
                 temperature: float = 0.0, 
                 max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Import here to avoid requiring the package if not used
        try:
            import anthropic
            self.client = anthropic.Anthropic()
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response using Anthropic Claude."""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        )


class OpenAIService(LLMService):
    """OpenAI API wrapper."""
    
    def __init__(self, model: str = "gpt-4o-mini", 
                 temperature: float = 0.0, 
                 max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            import openai
            self.client = openai.OpenAI()
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        )


class OllamaService(LLMService):
    """Ollama local LLM wrapper."""
    
    def __init__(self, model: str = "llama3.2", 
                 temperature: float = 0.0, 
                 max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            import ollama
            self.client = ollama
        except ImportError:
            raise ImportError("Please install ollama: pip install ollama")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response using Ollama."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.client.generate(
            model=self.model,
            prompt=full_prompt,
            options={
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        )
        
        return LLMResponse(
            content=response["response"],
            model=self.model,
            usage=None
        )


def create_llm_service(config_path: str = "config.yaml") -> LLMService:
    """Factory function to create LLM service from config file."""
    
    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "anthropic")
    model = llm_config.get("model")
    temperature = llm_config.get("temperature", 0.0)
    max_tokens = llm_config.get("max_tokens", 2000)
    
    if provider == "anthropic":
        return AnthropicService(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif provider == "openai":
        return OpenAIService(
            model=model or "gpt-4o-mini",
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif provider == "ollama":
        return OllamaService(
            model=model or "llama3.2",
            temperature=temperature,
            max_tokens=max_tokens
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


if __name__ == "__main__":
    # Simple test
    service = create_llm_service()
    response = service.generate("Say hello in one word.")
    print(f"Model: {response.model}")
    print(f"Response: {response.content}")
    print(f"Usage: {response.usage}")
