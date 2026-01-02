"""
Enum definitions for simple-sensor-network example.

This module demonstrates all EnumDef features:
- Basic enum: SensorType (simple enum with values)
- String mapping: AlertLevel (with fromString() helper)
- Bitflags: SensorCapabilities (combinable flags)
"""

from protocol_codegen.core.enum_def import EnumDef

# ============================================================================
# BASIC ENUM - SensorType
# ============================================================================
# Simple enum for sensor classification
# Generated as enum class in C++ and enum in Java

SensorType = EnumDef(
    name="SensorType",
    values={
        "UNKNOWN": 0,
        "TEMPERATURE": 1,
        "HUMIDITY": 2,
        "PRESSURE": 3,
        "LIGHT": 4,
        "MOTION": 5,
        "PROXIMITY": 6,
    },
    description="Type of sensor for classification",
)

# ============================================================================
# ENUM WITH STRING MAPPING - AlertLevel
# ============================================================================
# Enum with string_mapping generates fromString() helper in Java
# Useful for parsing API responses or configuration files

AlertLevel = EnumDef(
    name="AlertLevel",
    values={
        "NONE": 0,
        "INFO": 1,
        "WARNING": 2,
        "CRITICAL": 3,
    },
    description="Alert severity level",
    string_mapping={
        "none": "NONE",
        "info": "INFO",
        "warning": "WARNING",
        "critical": "CRITICAL",
        # Also support uppercase variants
        "NONE": "NONE",
        "INFO": "INFO",
        "WARNING": "WARNING",
        "CRITICAL": "CRITICAL",
    },
)

# ============================================================================
# BITFLAGS ENUM - SensorCapabilities
# ============================================================================
# Bitflags generate constants instead of enum class
# Values can be combined with bitwise OR
# Example: CAN_READ | CAN_CONFIGURE = 0x05

SensorCapabilities = EnumDef(
    name="SensorCapabilities",
    values={
        "NONE": 0x00,
        "CAN_READ": 0x01,  # Sensor can be read
        "CAN_CONFIGURE": 0x02,  # Sensor can be configured
        "CAN_CALIBRATE": 0x04,  # Sensor can be calibrated
        "HAS_ALERT": 0x08,  # Sensor supports alerts
        "IS_WIRELESS": 0x10,  # Sensor is wireless
        "BATTERY_POWERED": 0x20,  # Sensor runs on battery
    },
    description="Sensor capability flags (combinable with bitwise OR)",
    is_bitflags=True,
)
