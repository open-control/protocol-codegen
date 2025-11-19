"""
Type definitions for plugin_paths configuration.

These types document the expected structure of PLUGIN_PATHS dict.
User code should NOT import these - they're for internal type checking only.
"""

from typing import TypedDict


class OutputCppPaths(TypedDict):
    """C++ output paths configuration"""

    base_path: str
    namespace: str
    structs: str


class OutputJavaPaths(TypedDict):
    """Java output paths configuration"""

    base_path: str
    package: str
    structs: str


class PluginPathsConfig(TypedDict):
    """
    Complete plugin paths configuration.

    Example:
        PLUGIN_PATHS = {
            'plugin_name': 'my-plugin',
            'plugin_display_name': 'My Plugin',
            'output_cpp': {
                'base_path': 'src/protocol',
                'namespace': 'Protocol',
                'structs': 'struct/',
            },
            'output_java': {
                'base_path': 'host/src/protocol',
                'package': 'protocol',
                'structs': 'struct/',
            },
        }
    """

    plugin_name: str
    plugin_display_name: str
    output_cpp: OutputCppPaths
    output_java: OutputJavaPaths
