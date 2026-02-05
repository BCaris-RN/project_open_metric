import logging
import os

import requests

# --- CONFIG ---
# Default to local Ollama instance (Free & Offline)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")  # Or "mistral", "gemma", etc.

logger = logging.getLogger("open_metric.creative")


class CreativeEngine:
    def generate_caption(self, topic: str, tone: str = "professional") -> str:
        """
        Generates a social media caption using a local LLM.
        """
        prompt = (
            "Act as a professional social media manager. "
            f"Write a {tone} LinkedIn post about: '{topic}'. "
            "Include 3 relevant hashtags. "
            "Keep it under 200 words. "
            "Do not include preamble like 'Here is the post', just the content."
        )

        try:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            }

            logger.info("Generating content for: %s", topic)
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "Error: No response text found.")

            return f"Error: LLM returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Is it running?"
        except Exception as exc:
            return f"Error generating content: {exc}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    engine = CreativeEngine()
    print(engine.generate_caption("The future of AI automation"))
