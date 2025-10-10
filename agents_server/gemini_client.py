# gemini_client.py
import os
import google.generativeai as genai
from typing import Optional

class GeminiClient:
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", api_key: Optional[str] = None):
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"