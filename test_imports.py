#!/usr/bin/env python3
"""
Test all module imports individually to ensure no broken dependencies
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("="*70)
print("Testing Individual Module Imports")
print("="*70)
print()

tests = [
    # Core modules
    ("Core types", "protocol_codegen.core.types", ["BUILTIN_TYPES"]),
    ("Core field", "protocol_codegen.core.field", ["PrimitiveField", "CompositeField", "Type"]),
    ("Core message", "protocol_codegen.core.message", ["Message"]),
    ("Core loader", "protocol_codegen.core.loader", ["TypeRegistry"]),
    ("Core validator", "protocol_codegen.core.validator", ["ProtocolValidator"]),
    ("Core allocator", "protocol_codegen.core.allocator", ["allocate_message_ids"]),
    ("Core importer", "protocol_codegen.core.importer", ["import_sysex_messages"]),

    # SysEx method
    ("SysEx config", "protocol_codegen.methods.sysex.config", ["SysExConfig"]),
    ("SysEx builtin config", "protocol_codegen.methods.sysex.builtin_config", ["BUILTIN_SYSEX_CONFIG"]),

    # C++ generators
    ("C++ encoder gen", "protocol_codegen.generators.cpp.encoder_generator", ["generate_encoder_hpp"]),
    ("C++ decoder gen", "protocol_codegen.generators.cpp.decoder_generator", ["generate_decoder_hpp"]),
    ("C++ messageid gen", "protocol_codegen.generators.cpp.messageid_generator", ["generate_messageid_hpp"]),
    ("C++ struct gen", "protocol_codegen.generators.cpp.struct_generator", ["generate_struct_hpp"]),
    ("C++ constants gen", "protocol_codegen.generators.cpp.constants_generator", ["generate_constants_hpp"]),

    # Java generators
    ("Java encoder gen", "protocol_codegen.generators.java.encoder_generator", ["generate_encoder_java"]),
    ("Java decoder gen", "protocol_codegen.generators.java.decoder_generator", ["generate_decoder_java"]),
    ("Java messageid gen", "protocol_codegen.generators.java.messageid_generator", ["generate_messageid_java"]),
    ("Java struct gen", "protocol_codegen.generators.java.struct_generator", ["generate_struct_java"]),
    ("Java constants gen", "protocol_codegen.generators.java.constants_generator", ["generate_constants_java"]),
]

passed = 0
failed = 0
errors = []

for name, module_path, expected_exports in tests:
    try:
        module = __import__(module_path, fromlist=expected_exports)

        # Check expected exports exist
        missing = []
        for export in expected_exports:
            if not hasattr(module, export):
                missing.append(export)

        if missing:
            print(f"[PARTIAL] {name}")
            print(f"  Module: {module_path}")
            print(f"  Missing: {', '.join(missing)}")
            failed += 1
            errors.append((name, f"Missing exports: {missing}"))
        else:
            print(f"[OK] {name}")
            passed += 1

    except Exception as e:
        print(f"[FAIL] {name}")
        print(f"  Error: {e}")
        failed += 1
        errors.append((name, str(e)))

print()
print("="*70)
print(f"Results: {passed} passed, {failed} failed")
print("="*70)

if errors:
    print()
    print("Failed tests:")
    for name, error in errors:
        print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print()
    print("✓ All module imports working!")
