"""
Renderers Package.

Provides file renderers organized by dependency type:
- universal/: Depend on both backend and strategy
- by_backend/: Depend only on backend (language)
- by_backend_strategy/: Depend on both, but logic differs
- protocol/: Protocol template renderers (mixin-based)
"""

from protocol_codegen.generators.compositions.base import (
    BackendRenderer,
    BackendStrategyRenderer,
    FileRenderer,
)
from protocol_codegen.generators.compositions.registry import (
    RendererRegistry,
    get_renderer,
    register_renderer,
)

__all__ = [
    # Base classes
    "FileRenderer",
    "BackendRenderer",
    "BackendStrategyRenderer",
    # Registry
    "RendererRegistry",
    "get_renderer",
    "register_renderer",
]
