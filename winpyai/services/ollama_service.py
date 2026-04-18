"""Ollama HTTP API client service for WinPyAI."""

import json
import logging
from typing import Any, Generator

import requests

from winpyai.config import OLLAMA_HOST

logger = logging.getLogger(__name__)


class OllamaConnectionError(Exception):
    """Raised when the Ollama server cannot be reached or connection fails."""

    def __init__(self, message: str = "Cannot connect to Ollama server") -> None:
        self.message = message
        super().__init__(self.message)


class OllamaModelError(Exception):
    """Raised when the requested model is not found or not available."""

    def __init__(self, message: str = "Model not found") -> None:
        self.message = message
        super().__init__(self.message)


class OllamaResponseError(Exception):
    """Raised when the Ollama API returns an invalid or unexpected response."""

    def __init__(self, message: str = "Invalid response from Ollama") -> None:
        self.message = message
        super().__init__(self.message)


class OllamaService:
    """Service layer for communicating with the Ollama HTTP API."""

    CONNECT_TIMEOUT: float = 5.0
    READ_TIMEOUT: float = 60.0
    READ_TIMEOUT_STREAM: float = 60.0
    HEALTH_TIMEOUT: float = 2.0

    def __init__(self, host: str = OLLAMA_HOST) -> None:
        """Initialize the Ollama service.

        Args:
            host: Base URL of the Ollama server (default: http://localhost:11434).
        """
        self.host = host.rstrip("/")
        logger.debug("OllamaService initialized with host=%s", self.host)

    def _url(self, path: str) -> str:
        """Build a full URL from an API path.

        Args:
            path: The API endpoint path (e.g., '/api/tags').

        Returns:
            str: The full URL string.
        """
        return f"{self.host}{path}"

    def is_running(self) -> bool:
        """Check if the Ollama server is reachable.

        Returns:
            bool: True if the server responds within the health timeout, False otherwise.
        """
        try:
            response = requests.get(
                self._url("/api/tags"),
                timeout=(self.CONNECT_TIMEOUT, self.HEALTH_TIMEOUT),
            )
            return response.status_code == 200
        except Exception:
            logger.debug("Ollama health check failed", exc_info=True)
            return False

    def list_models(self) -> list[str]:
        """GET /api/tags — return list of installed model names.

        Returns:
            list[str]: List of installed model names. Empty list if Ollama
                is not running or no models are installed.
        """
        if not self.is_running():
            logger.warning("Cannot list models: Ollama is not running")
            return []

        try:
            response = requests.get(
                self._url("/api/tags"),
                timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT),
            )
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            names = [model.get("name", "") for model in models if model.get("name")]
            logger.debug("Found %d models", len(names))
            return names
        except requests.RequestException as exc:
            logger.error("Failed to list models: %s", exc)
            return []
        except (ValueError, KeyError, TypeError) as exc:
            logger.error("Failed to parse model list: %s", exc)
            return []

    def chat_stream(
        self, model: str, messages: list[dict], system: str = ""
    ) -> Generator[str, None, None]:
        """POST /api/chat with stream=True. Yields token strings.

        Sends a chat completion request to Ollama and yields each token chunk
        as it is received, enabling real-time streaming of the response.

        Args:
            model: The Ollama model name to use (e.g., 'llama3.2:latest').
            messages: List of message dicts with 'role' and 'content' keys.
            system: Optional system prompt to prepend to the conversation.

        Yields:
            str: Each token string from the streaming response.

        Raises:
            OllamaConnectionError: If the connection to Ollama fails.
            OllamaModelError: If the requested model is not found (HTTP 404).
            OllamaResponseError: If the response cannot be parsed.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {},
        }
        if system:
            payload["system"] = system

        logger.debug("chat_stream request model=%s messages=%d", model, len(messages))

        try:
            response = requests.post(
                self._url("/api/chat"),
                json=payload,
                stream=True,
                timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT_STREAM),
            )
        except requests.ConnectionError as exc:
            logger.error("Connection to Ollama failed: %s", exc)
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.host}") from exc
        except requests.Timeout as exc:
            logger.error("Connection to Ollama timed out: %s", exc)
            raise OllamaConnectionError(f"Connection to Ollama at {self.host} timed out") from exc
        except requests.RequestException as exc:
            logger.error("Request to Ollama failed: %s", exc)
            raise OllamaConnectionError(f"Request to Ollama failed: {exc}") from exc

        if response.status_code == 404:
            logger.error("Model not found: %s", model)
            raise OllamaModelError(f"Model '{model}' not found. Run 'ollama pull {model}' to download it.")

        if response.status_code != 200:
            logger.error("Ollama returned status %d", response.status_code)
            raise OllamaResponseError(f"Ollama returned HTTP {response.status_code}")

        # Parse JSON Lines response
        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    chunk_data = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed JSON line: %s", line[:200])
                    continue

                # Check for completion
                if chunk_data.get("done", False):
                    break

                # Extract token content
                message_chunk = chunk_data.get("message", {})
                token = message_chunk.get("content", "")
                if token:
                    yield token

        except requests.RequestException as exc:
            logger.error("Stream interrupted: %s", exc)
            raise OllamaConnectionError(f"Stream interrupted: {exc}") from exc
        except (OllamaConnectionError, OllamaModelError):
            raise
        except Exception as exc:
            logger.error("Unexpected error while reading stream: %s", exc)
            raise OllamaResponseError(f"Unexpected error reading stream: {exc}") from exc
        finally:
            response.close()

    def chat(self, model: str, messages: list[dict], system: str = "") -> str:
        """POST /api/chat with stream=False. Returns full response.

        Sends a chat completion request to Ollama and returns the complete
        response as a single string.

        Args:
            model: The Ollama model name to use.
            messages: List of message dicts with 'role' and 'content' keys.
            system: Optional system prompt to prepend to the conversation.

        Returns:
            str: The full assistant response text.

        Raises:
            OllamaConnectionError: If the connection to Ollama fails.
            OllamaModelError: If the requested model is not found (HTTP 404).
            OllamaResponseError: If the response cannot be parsed.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {},
        }
        if system:
            payload["system"] = system

        logger.debug("chat request model=%s messages=%d", model, len(messages))

        try:
            response = requests.post(
                self._url("/api/chat"),
                json=payload,
                timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT),
            )
        except requests.ConnectionError as exc:
            logger.error("Connection to Ollama failed: %s", exc)
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.host}") from exc
        except requests.Timeout as exc:
            logger.error("Connection to Ollama timed out: %s", exc)
            raise OllamaConnectionError(f"Connection to Ollama at {self.host} timed out") from exc
        except requests.RequestException as exc:
            logger.error("Request to Ollama failed: %s", exc)
            raise OllamaConnectionError(f"Request to Ollama failed: {exc}") from exc

        if response.status_code == 404:
            logger.error("Model not found: %s", model)
            raise OllamaModelError(f"Model '{model}' not found. Run 'ollama pull {model}' to download it.")

        if response.status_code != 200:
            logger.error("Ollama returned status %d", response.status_code)
            raise OllamaResponseError(f"Ollama returned HTTP {response.status_code}")

        try:
            data = response.json()
        except (ValueError, TypeError) as exc:
            logger.error("Failed to parse JSON response: %s", exc)
            raise OllamaResponseError(f"Invalid JSON response: {exc}") from exc

        message = data.get("message", {})
        content = message.get("content", "") if isinstance(message, dict) else ""
        logger.debug("chat response length=%d chars", len(content))
        return content

    def pull_model(self, model: str) -> bool:
        """POST /api/pull to download a model.

        Args:
            model: The model name to pull from the Ollama registry.

        Returns:
            bool: True if the pull was successful, False otherwise.
        """
        logger.info("Pulling model: %s", model)
        try:
            response = requests.post(
                self._url("/api/pull"),
                json={"name": model, "stream": False},
                timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT),
            )
            if response.status_code == 200:
                logger.info("Successfully pulled model: %s", model)
                return True
            else:
                logger.error("Failed to pull model %s: HTTP %d", model, response.status_code)
                return False
        except requests.RequestException as exc:
            logger.error("Failed to pull model %s: %s", model, exc)
            return False

    def get_status(self) -> dict:
        """Get the current Ollama server status.

        Returns:
            dict: A dictionary with keys:
                - running (bool): Whether Ollama is reachable.
                - models (list[str]): List of installed model names.
                - error (str | None): Error message if not running, None otherwise.
        """
        running = self.is_running()
        if not running:
            return {
                "running": False,
                "models": [],
                "error": f"Ollama server not reachable at {self.host}",
            }

        models = self.list_models()
        return {
            "running": True,
            "models": models,
            "error": None,
        }
