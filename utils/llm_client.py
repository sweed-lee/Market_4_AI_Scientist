"""
Simple OpenAI client wrapper with support for custom base URL.

This module provides a simple wrapper around OpenAI client with support for
custom base URLs (e.g., local LLM servers, proxies, etc.).
"""

from typing import Optional
import openai


class LLMClient:
    """
    Simple OpenAI-compatible LLM client.
    
    Usage:
        # Standard OpenAI
        client = LLMClient(api_key='your-key', model='gpt-4')
        
        # With custom base URL (e.g., local LLM)
        client = LLMClient(
            api_key='your-key',
            model='llama-2-7b',
            base_url='http://localhost:8000/v1'
        )
        
        # Generate response
        response = client.generate("Your prompt here")
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", 
                 base_url: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (can be dummy for local servers)
            model: Model name to use
            base_url: Custom base URL for OpenAI-compatible APIs
                      If None, uses default OpenAI endpoint
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        
        if self.base_url:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = openai.OpenAI(
                api_key=self.api_key,
            )
    
    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Input prompt text
            model: Optional model override for this call
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated text response
        """
        # print(prompt)
        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        # print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def __repr__(self) -> str:
        base_url_display = self.base_url if self.base_url else "default"
        return f"LLMClient(model='{self.model}', base_url='{base_url_display}')"
