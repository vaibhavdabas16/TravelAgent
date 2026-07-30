"""Google Gemini API client service.

Provides text generation and structured output capabilities using the
google-generativeai library.
"""
import logging
import json
import re
from typing import Optional, Any
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Client for Google Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client with API keys from settings."""
        self.api_keys = settings.gemini_api_keys
        if not self.api_keys:
            logger.warning("No Gemini API keys found in settings!")
            # Fallback to single key if property fails for some reason
            if settings.gemini_api_key:
                self.api_keys = [settings.gemini_api_key]
        
        self.current_key_index = 0
        self._configure_client()
        logger.info(f"GeminiService initialized with {len(self.api_keys)} keys")

    def _configure_client(self):
        """Configure the Gemini client with the current API key."""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        # logger.info(f"Switched to Gemini API key index: {self.current_key_index}")

    def _rotate_key(self):
        """Rotate to the next available API key."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._configure_client()
            logger.info(f"Rotated Gemini API key to index {self.current_key_index}")
            return True
        return False
    
    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        retry_count: int = 0
    ) -> str:
        """
        Generate text response from a prompt.
        
        Args:
            prompt: The input prompt for the model
            temperature: Controls randomness (0.0-1.0). Lower = more deterministic.
            max_output_tokens: Maximum length of the response
            retry_count: Internal retry counter (don't set manually)
            
        Returns:
            Generated text response
            
        Example:
            >>> service = GeminiService()
            >>> response = service.generate("What are the top 3 attractions in Paris?")
            >>> print(response)
        """
        import time
        
        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            result = response.text
            logger.info(f"Generated response ({len(result)} chars) for prompt")
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                # Try rotating key first
                if self._rotate_key():
                    logger.warning(f"Gemini API rate limit hit, rotated key and retrying...")
                    return self.generate(prompt, temperature, max_output_tokens, retry_count)
                
                # If no more keys or rotation didn't help, try backoff
                if retry_count < 2:  # Try up to 2 retries
                    wait_time = (2 ** retry_count) * 2  # Exponential backoff: 2s, 4s
                    logger.warning(f"Gemini API rate limit hit, waiting {wait_time}s before retry {retry_count + 1}/2")
                    time.sleep(wait_time)
                    return self.generate(prompt, temperature, max_output_tokens, retry_count + 1)
                else:
                    logger.error(f"Gemini API rate limit exceeded after retries.")
                    logger.info("💡 Tip: Consider upgrading your Gemini API quota at https://ai.google.dev/pricing")
            
            logger.error(f"Error generating content with Gemini: {e}")
            raise
    
    def generate_structured(
        self, 
        prompt: str, 
        temperature: float = 0.1,
        max_output_tokens: int = 8192,
        retry_count: int = 0
    ) -> dict:
        """
        Generate structured JSON output from a prompt.
        
        This method expects the prompt to request JSON output and will
        attempt to parse the response as JSON.
        
        Args:
            prompt: The input prompt (should request JSON format)
            temperature: Lower temperature for more deterministic structured output
            max_output_tokens: Maximum length of the response
            retry_count: Internal retry counter (don't set manually)
            
        Returns:
            Parsed JSON object as a dictionary
            
        Raises:
            ValueError: If the response cannot be parsed as JSON
            
        Example:
            >>> prompt = '''Extract trip details as JSON:
            ... User: "I want to visit Tokyo for 5 days"
            ... Return only JSON with keys: destination, duration_days'''
            >>> result = service.generate_structured(prompt)
            >>> print(result)
            {'destination': 'Tokyo', 'duration_days': 5}
        """
        import time
        
        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            response_text = response.text.strip()
            
            # Try to parse as JSON directly
            try:
                result = json.loads(response_text)
                logger.info("Successfully parsed structured JSON response")
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    logger.info("Extracted and parsed JSON from markdown code block")
                    return result
                
                # Try to find any JSON object in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    logger.info("Extracted and parsed JSON object from response")
                    return result
                
                # If all parsing attempts fail
                logger.error(f"Could not parse JSON from response: {response_text[:200]}")
                raise ValueError(f"Could not extract valid JSON from response: {response_text[:200]}...")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON in response: {e}")
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                # Try rotating key first
                if self._rotate_key():
                    logger.warning(f"Gemini API rate limit hit, rotated key and retrying...")
                    return self.generate_structured(prompt, temperature, max_output_tokens, retry_count)

                if retry_count < 2:  # Try up to 2 retries
                    wait_time = (2 ** retry_count) * 2  # Exponential backoff: 2s, 4s
                    logger.warning(f"Gemini API rate limit hit, waiting {wait_time}s before retry {retry_count + 1}/2")
                    time.sleep(wait_time)
                    return self.generate_structured(prompt, temperature, max_output_tokens, retry_count + 1)
                else:
                    logger.error(f"Gemini API rate limit exceeded after retries.")
                    logger.info("💡 Tip: Consider upgrading your Gemini API quota at https://ai.google.dev/pricing")
            
            logger.error(f"Error generating structured content with Gemini: {e}")
            raise
    
    def generate_with_context(
        self,
        system_instruction: str,
        user_message: str,
        temperature: float = 0.3
    ) -> str:
        """
        Generate response with system instruction context.
        
        Args:
            system_instruction: System-level instruction defining agent role/behavior
            user_message: The user's actual query
            temperature: Controls randomness
            
        Returns:
            Generated text response
        """
        combined_prompt = f"{system_instruction}\n\nUser: {user_message}\n\nAssistant:"
        return self.generate(combined_prompt, temperature=temperature)


# Global service instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the global GeminiService instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

