"""StreamWorker — QThread for streaming Ollama chat responses."""

import logging

from PyQt6.QtCore import QThread, pyqtSignal

from winpyai.services.ollama_service import (
    OllamaConnectionError,
    OllamaModelError,
    OllamaResponseError,
    OllamaService,
)

logger = logging.getLogger(__name__)


class StreamWorker(QThread):
    """Worker thread that streams chat responses from Ollama.

    Runs in a separate thread to avoid blocking the UI. Emits each token
    chunk as it arrives, and the full accumulated response when complete.

    Signals:
        chunk_received(str): Emitted for each token chunk received.
        finished_signal(str): Emitted with the full accumulated response when done.
        error_occurred(str): Emitted if an error occurs during streaming.
    """

    chunk_received = pyqtSignal(str)       # Each token chunk
    finished_signal = pyqtSignal(str)      # Full accumulated response
    error_occurred = pyqtSignal(str)       # Error message string

    def __init__(
        self,
        ollama_service: OllamaService,
        model: str,
        messages: list[dict],
        system: str = "",
        parent=None,
    ) -> None:
        """Initialize the StreamWorker.

        Args:
            ollama_service: The OllamaService instance to use for streaming.
            model: The Ollama model name to chat with.
            messages: List of message dicts with 'role' and 'content' keys.
            system: Optional system prompt to send with the request.
            parent: Optional parent QObject for Qt lifecycle management.
        """
        super().__init__(parent)
        self.ollama = ollama_service
        self.model = model
        self.messages = messages
        self.system = system
        self._stop_flag = False
        self._full_response = ""

    def run(self) -> None:
        """Call ollama.chat_stream(), emit each chunk, accumulate full response.

        This method runs in a separate thread. It iterates over the streaming
        generator from Ollama, emitting each token chunk via the
        chunk_received signal. When the stream completes or is stopped, it
        emits the full accumulated response via finished_signal. On any
        exception, it emits the error message via error_occurred.
        """
        logger.debug(
            "StreamWorker started model=%s messages=%d",
            self.model,
            len(self.messages),
        )
        self._stop_flag = False
        self._full_response = ""

        try:
            for chunk in self.ollama.chat_stream(self.model, self.messages, self.system):
                if self._stop_flag:
                    logger.debug("StreamWorker stopped by flag")
                    break
                self._full_response += chunk
                self.chunk_received.emit(chunk)
            self.finished_signal.emit(self._full_response)
            logger.debug(
                "StreamWorker finished response_length=%d",
                len(self._full_response),
            )
        except OllamaConnectionError as exc:
            logger.error("StreamWorker connection error: %s", exc)
            self.error_occurred.emit(f"Connection error: {exc}")
        except OllamaModelError as exc:
            logger.error("StreamWorker model error: %s", exc)
            self.error_occurred.emit(f"Model error: {exc}")
        except OllamaResponseError as exc:
            logger.error("StreamWorker response error: %s", exc)
            self.error_occurred.emit(f"Response error: {exc}")
        except Exception as exc:
            logger.error("StreamWorker unexpected error: %s", exc)
            self.error_occurred.emit(str(exc))

    def stop(self) -> None:
        """Set the stop flag to break the stream loop.

        The stream will stop at the next iteration of the generator loop.
        The partial response accumulated so far will still be emitted via
        finished_signal.
        """
        logger.debug("StreamWorker stop requested")
        self._stop_flag = True
