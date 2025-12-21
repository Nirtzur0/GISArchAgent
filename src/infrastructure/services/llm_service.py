"""
LLM Service for answer synthesis using Gemini.
"""

import logging
from typing import Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiLLMService:
    """Service for generating answers using Gemini."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini LLM service.
        
        Args:
            api_key: Google AI API key
            model: Gemini model name
        """
        self.api_key = api_key
        self.model_name = model
        self.client = genai.Client(api_key=api_key)
        logger.info(f"Gemini LLM service initialized: {model}")
    
    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer based on question and context.
        
        Args:
            question: User's question
            context: Relevant regulations/context
            
        Returns:
            Generated answer
        """
        try:
            prompt = self._build_prompt(question, context)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )
            
            if response and response.text:
                return response.text.strip()
            
            return "Unable to generate answer from available regulations."
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error processing query: {str(e)}"
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt for answer generation."""
        return f"""You are an expert in Israeli planning and zoning regulations. Answer the user's question based on the provided regulations.

Regulations Context:
{context}

User Question: {question}

Instructions:
- Answer in a clear, professional manner
- Support your answer with specific regulation references
- If the regulations don't contain relevant information, say so
- Use Hebrew terms when appropriate but explain them
- Be concise but thorough

Answer:"""
