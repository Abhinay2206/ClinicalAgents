# llm_client.py
import os
import time
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class GrokClient:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        """
        Initialize Groq client for Llama 3.3 model
        
        Args:
            model_name: Groq model to use (default: "llama-3.3-70b-versatile")
            api_key: Groq API key (if not provided, will use GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        self.model_name = model_name
    
    def generate(self, prompt: str, max_tokens: int = 3000, temperature: float = 0.3, max_retries: int = 3) -> str:
        """
        Generate content with retry logic for rate limit errors
        
        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate (called max_completion_tokens in Groq)
            temperature: Sampling temperature (0.0-2.0)
            max_retries: Maximum number of retry attempts for rate limits
            
        Returns:
            Generated text response
        """
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a clinical research data analyst providing evidence-based educational information "
                                "for healthcare professionals, medical researchers, and clinical trial coordinators. "
                                "Provide detailed, comprehensive, and well-structured responses using markdown formatting, "
                                "tables, and specific metrics where appropriate."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=max_tokens,
                    temperature=temperature,
                    top_p=1,
                    stream=False
                )
                
                # Extract the response content
                if completion.choices and len(completion.choices) > 0:
                    return completion.choices[0].message.content
                else:
                    return "No response generated. Please try again with a different query."
                    
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                
                # Check if it's a rate limit error
                is_rate_limit = (
                    "429" in error_msg or 
                    "quota" in error_msg.lower() or 
                    "rate limit" in error_msg.lower() or
                    "rate_limit" in error_msg.lower() or
                    "resource exhausted" in error_msg.lower()
                )
                
                if is_rate_limit and retries < max_retries:
                    wait_time = 2 ** retries  # Exponential backoff: 1s, 2s, 4s
                    print(f"⚠️ Rate limit detected. Retry {retries + 1}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                elif is_rate_limit:
                    # Exhausted retries
                    print(f"❌ Rate limit exceeded after {max_retries} retries")
                    return "⚠️ API rate limit exceeded. Please wait a moment and try again. If this persists, consider spacing out your requests."
                else:
                    # Non-rate-limit error, fail immediately
                    print(f"Generation error: {error_msg}")
                    return f"Error generating response: {error_msg}"
        
        # Should not reach here, but just in case
        return f"Error generating response after retries: {last_error}"
