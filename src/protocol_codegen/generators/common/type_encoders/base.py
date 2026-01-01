"""
Type Encoder Base Class.

Defines the interface for type-specific encoding logic.
Each TypeEncoder knows how to produce a MethodSpec for its supported types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.generators.common.encoding import EncodingStrategy
    from protocol_codegen.generators.common.encoding.operations import MethodSpec


class TypeEncoder(ABC):
    """Base class for type-specific encoding logic.

    TypeEncoders are responsible for producing MethodSpecs that describe
    HOW to encode a type. They use an injected EncodingStrategy to get
    protocol-specific parameters (masks, shifts, byte counts).

    The MethodSpec is then rendered to actual code by a LanguageBackend.
    """

    def __init__(self, strategy: EncodingStrategy) -> None:
        """Initialize with encoding strategy.

        Args:
            strategy: Protocol-specific encoding parameters
        """
        self.strategy = strategy

    @abstractmethod
    def supported_types(self) -> tuple[str, ...]:
        """Return type names this encoder handles.

        Returns:
            Tuple of protocol-codegen type names (e.g., ("uint8", "uint16"))
        """
        ...

    @abstractmethod
    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate method specification for the given type.

        Args:
            type_name: Protocol-codegen type name
            description: Human-readable description from TypeRegistry

        Returns:
            MethodSpec describing how to encode this type

        Raises:
            ValueError: If type_name is not in supported_types()
        """
        ...
