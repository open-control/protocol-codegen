from protocol_codegen.core.field import PrimitiveField, Type

# ============================================================================
# COLOR FIELDS
# ============================================================================
# RGB color encoded as uint32 (0xRRGGBB)
# Example: Red = 0xFF0000, Green = 0x00FF00, Blue = 0x0000FF

color_rgb = PrimitiveField('color', type_name=Type.UINT32)
