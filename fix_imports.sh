#!/bin/bash
# Systematic import fix script for protocol-codegen
# Fixes all "protocol.*" imports to "protocol_codegen.*"

set -e

echo "=========================================="
echo "Protocol CodeGen - Import Fix Script"
echo "=========================================="
echo

cd "$(dirname "$0")/src/protocol_codegen"

# Count before
BEFORE=$(grep -r "from protocol\." . --include="*.py" | wc -l)
echo "Imports to fix: $BEFORE"
echo

# Fix all imports systematically
echo "[1/8] Fixing protocol.type_loader → protocol_codegen.core.loader"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.type_loader import/from protocol_codegen.core.loader import/g' {} \;

echo "[2/8] Fixing protocol.message_importer → protocol_codegen.core.importer"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.message_importer import/from protocol_codegen.core.importer import/g' {} \;

echo "[3/8] Fixing protocol.message_id_allocator → protocol_codegen.core.allocator"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.message_id_allocator import/from protocol_codegen.core.allocator import/g' {} \;

echo "[4/8] Fixing protocol.message → protocol_codegen.core.message"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.message import/from protocol_codegen.core.message import/g' {} \;

echo "[5/8] Fixing protocol.field → protocol_codegen.core.field"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.field import/from protocol_codegen.core.field import/g' {} \;

echo "[6/8] Fixing protocol.validator → protocol_codegen.core.validator"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.validator import/from protocol_codegen.core.validator import/g' {} \;

echo "[7/8] Fixing protocol.generators.cpp → protocol_codegen.generators.cpp"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.generators\.cpp/from protocol_codegen.generators.cpp/g' {} \;

echo "[8/8] Fixing protocol.generators.java → protocol_codegen.generators.java"
find . -name "*.py" -type f -exec sed -i 's/from protocol\.generators\.java/from protocol_codegen.generators.java/g' {} \;

# Count after
AFTER=$(grep -r "from protocol\." . --include="*.py" | wc -l || echo "0")
echo
echo "=========================================="
echo "Imports fixed: $BEFORE → $AFTER"
if [ "$AFTER" -eq "0" ]; then
    echo "✓ All imports fixed successfully!"
else
    echo "⚠ $AFTER imports still need manual review:"
    grep -r "from protocol\." . --include="*.py" || true
fi
echo "=========================================="
