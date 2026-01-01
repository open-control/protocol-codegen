"""
Renderer Registry.

Auto-discovery and factory for renderers.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class RendererRegistry:
    """
    Registry for file renderers.

    Supports registration by:
    - (file_type, backend_name) for by_backend renderers
    - (file_type, backend_name, strategy_name) for by_backend_strategy renderers
    """

    _by_backend: dict[tuple[str, str], type[Any]] = {}
    _by_backend_strategy: dict[tuple[str, str, str], type[Any]] = {}

    @classmethod
    def register_backend(
        cls,
        file_type: str,
        backend_name: str,
    ) -> Callable[[type[Any]], type[Any]]:
        """Decorator to register a by_backend renderer."""

        def decorator(renderer_cls: type[Any]) -> type[Any]:
            key = (file_type, backend_name.lower())
            cls._by_backend[key] = renderer_cls
            return renderer_cls

        return decorator

    @classmethod
    def register_backend_strategy(
        cls,
        file_type: str,
        backend_name: str,
        strategy_name: str,
    ) -> Callable[[type[Any]], type[Any]]:
        """Decorator to register a by_backend_strategy renderer."""

        def decorator(renderer_cls: type[Any]) -> type[Any]:
            key = (file_type, backend_name.lower(), strategy_name.lower())
            cls._by_backend_strategy[key] = renderer_cls
            return renderer_cls

        return decorator

    @classmethod
    def get_backend_renderer(
        cls,
        file_type: str,
        backend: "LanguageBackend",
    ) -> Any:
        """Get a by_backend renderer instance."""
        key = (file_type, backend.name.lower())
        if key not in cls._by_backend:
            raise ValueError(f"No renderer registered for ({file_type}, {backend.name})")
        return cls._by_backend[key](backend)

    @classmethod
    def get_backend_strategy_renderer(
        cls,
        file_type: str,
        backend: "LanguageBackend",
        strategy: "EncodingStrategy",
    ) -> Any:
        """Get a by_backend_strategy renderer instance."""
        key = (file_type, backend.name.lower(), strategy.name.lower())
        if key not in cls._by_backend_strategy:
            raise ValueError(
                f"No renderer registered for ({file_type}, {backend.name}, {strategy.name})"
            )
        return cls._by_backend_strategy[key](backend, strategy)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered renderers (useful for testing)."""
        cls._by_backend.clear()
        cls._by_backend_strategy.clear()


# Convenience functions
def register_renderer(
    file_type: str,
    backend_name: str,
    strategy_name: str | None = None,
) -> Callable[[type[Any]], type[Any]]:
    """
    Decorator to register a renderer.

    Usage:
        @register_renderer("enum", "cpp")
        class CppEnumRenderer: ...

        @register_renderer("struct", "java", "sysex")
        class JavaSysExStructRenderer: ...
    """
    if strategy_name is None:
        return RendererRegistry.register_backend(file_type, backend_name)
    return RendererRegistry.register_backend_strategy(file_type, backend_name, strategy_name)


def get_renderer(
    file_type: str,
    backend: "LanguageBackend",
    strategy: "EncodingStrategy | None" = None,
) -> Any:
    """
    Get a renderer instance.

    Usage:
        renderer = get_renderer("enum", cpp_backend)
        renderer = get_renderer("struct", java_backend, sysex_strategy)
    """
    if strategy is None:
        return RendererRegistry.get_backend_renderer(file_type, backend)
    return RendererRegistry.get_backend_strategy_renderer(file_type, backend, strategy)


__all__ = [
    "RendererRegistry",
    "register_renderer",
    "get_renderer",
]
