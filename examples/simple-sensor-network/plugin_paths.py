"""
Output Paths Configuration

Defines where to generate the C++ and Java code.

Configuration Structure:
- output_cpp: C++ generation settings
  - base_path: Root directory for C++ files
  - namespace: C++ namespace for generated code
  - structs: Subdirectory for message structs (relative to base_path)

- output_java: Java generation settings
  - base_path: Root directory for Java files
  - package: Java package name for generated code
  - structs: Subdirectory for message classes (relative to base_path)
"""

PLUGIN_PATHS = {
    "plugin_name": "sensor-network",
    "plugin_display_name": "Sensor Network Example",
    "output_cpp": {
        "base_path": "generated/cpp",
        "namespace": "SensorProtocol",
        "structs": "struct/",
    },
    "output_java": {
        "base_path": "generated/java/com/example/sensor",
        "package": "com.example.sensor",
        "structs": "struct/",
    },
}
