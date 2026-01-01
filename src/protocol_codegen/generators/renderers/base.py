"""
Base Renderer Classes.

Abstract base classes for all file renderers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class FileRenderer(ABC):
    """
    Abstract base class for all file renderers.

    A renderer generates a single output file from input data.
    """

    @property
    @abstractmethod
    def file_type(self) -> str:
        """Return the type of file this renderer produces (e.g., 'enum', 'struct')."""
        ...

    @abstractmethod
    def render(self, data: Any, output_path: Path, **kwargs: Any) -> str:
        """
        Render the file content.

        Args:
            data: Input data (message, enum_def, etc.)
            output_path: Target file path
            **kwargs: Additional renderer-specific arguments

        Returns:
            Generated file content as string
        """
        ...


class BackendRenderer(FileRenderer):
    """
    Base class for renderers that depend only on backend.

    Examples: EnumRenderer, CallbacksRenderer, MessageIdRenderer
    """

    def __init__(self, backend: "LanguageBackend") -> None:
        self.backend = backend

    @property
    def language(self) -> str:
        """Return the target language name."""
        return self.backend.name


class BackendStrategyRenderer(FileRenderer):
    """
    Base class for renderers that depend on both backend and strategy.

    Examples: StructRenderer, ConstantsRenderer
    """

    def __init__(
        self,
        backend: "LanguageBackend",
        strategy: "EncodingStrategy",
    ) -> None:
        self.backend = backend
        self.strategy = strategy

    @property
    def language(self) -> str:
        """Return the target language name."""
        return self.backend.name

    @property
    def protocol(self) -> str:
        """Return the protocol name."""
        return self.strategy.name


__all__ = [
    "FileRenderer",
    "BackendRenderer",
    "BackendStrategyRenderer",
]
