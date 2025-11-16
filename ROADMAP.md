# Protocol CodeGen - Roadmap

## Current Status

**Version:** 1.0.0 (extraction phase)
**Status:** Files migrated, refactoring needed
**Priority:** Make it functional as standalone package first

---

## Phase 1: Make It Work (HIGH PRIORITY)

### 1.1 Fix Imports & Dependencies
- [ ] Update all imports (protocol.* → protocol_codegen.*)
- [ ] Create sysex/generator.py orchestrator
- [ ] Fix any path hardcoding
- [ ] Ensure zero MIDI Studio dependencies

### 1.2 Basic Testing
- [ ] Test CLI commands
- [ ] Generate code for simple test protocol
- [ ] Verify C++ compilation
- [ ] Verify Java compilation

### 1.3 Documentation
- [ ] Complete getting-started guide
- [ ] Add simple example (Arduino + Python)
- [ ] Document message definition syntax

**Timeline:** ASAP (current phase)
**Status:** 🔄 In Progress

---

## Phase 2: Make It Right (MEDIUM PRIORITY)

### 2.1 Code Quality
- [ ] Add unit tests (pytest)
- [ ] Add integration tests
- [ ] Setup CI/CD (GitHub Actions)
- [ ] Code coverage > 70%

### 2.2 Examples & Docs
- [ ] Complete sysex-teensy-java example
- [ ] Add sysex-arduino-python example
- [ ] Write comprehensive documentation
- [ ] Create video tutorial

### 2.3 Publication
- [ ] Publish to PyPI
- [ ] Create GitHub releases
- [ ] Announce to community

**Timeline:** After Phase 1 complete
**Status:** ⏸️ Pending

---

## Phase 3: Make It Fast (LOW PRIORITY)

### 3.1 Performance Optimizations
- [ ] Optimize code generation speed
- [ ] Reduce generated code size
- [ ] Benchmark encoding/decoding performance

### 3.2 Developer Experience
- [ ] Better error messages
- [ ] Auto-completion for message definitions
- [ ] Live reload during development

**Timeline:** After Phase 2
**Status:** ⏸️ Pending

---

## Future Features (PLANNED)

### OSC Support (LOW PRIORITY)
- [ ] OSC message encoding/decoding
- [ ] OSC bundle support
- [ ] Type tags handling
- [ ] Timestamp synchronization

**Rationale:** OSC is common in audio/video applications
**Effort:** Medium (2-3 weeks)
**Value:** High for audio developers
**Status:** 📋 Planned

---

### Python Code Generator (LOW PRIORITY)
- [ ] Python encoder/decoder generation
- [ ] Type hints support
- [ ] Dataclasses for messages
- [ ] Integration with existing Python ecosystem

**Rationale:** Python is widely used for scripting, testing, and host applications
**Effort:** Medium (1-2 weeks)
**Value:** High for rapid prototyping and testing
**Status:** 📋 Planned

---

## Architecture Evolution (LOW PRIORITY, IMPORTANT)

### Protobuf Integration Strategy

**Current Architecture:**
```
User defines messages in Python
    ↓
Protocol CodeGen generates everything
    - Type system
    - Validation
    - Multi-language code generation
    - Transport encoding (SysEx, OSC, etc.)
```

**Proposed Future Architecture:**
```
User defines messages in .proto (Protobuf)
    ↓
protoc generates multi-language code (C++, Java, Python, Rust, Go, etc.)
    ↓
Protocol CodeGen generates ONLY transport adapters
    - SysExAdapter: Protobuf ↔ SysEx (7-bit, F0/F7, manufacturer ID)
    - OSCAdapter: Protobuf ↔ OSC (type tags, bundles, timestamps)
```

**Why This Makes Sense:**

✅ **Leverage Protobuf Ecosystem**
- Multi-language support for FREE (20+ languages via protoc)
- Battle-tested type system and validation
- Backward compatibility built-in
- IDE support and tooling
- Industry-standard .proto syntax

✅ **Protocol CodeGen Focuses on True Value**
- Generate transport layer adapters (SysEx, OSC)
- Handle protocol-specific constraints:
  - SysEx: 7-bit encoding, F0/F7 framing, manufacturer IDs
  - OSC: Type tags, bundles, timestamps
- Smaller, more focused codebase

✅ **Clearer Value Proposition**
- Not competing with Protobuf
- Complementary tool for specialized transports
- "Use Protobuf for messages, Protocol CodeGen for MIDI/OSC/etc."

**Example Workflow:**

```bash
# 1. Define messages (Protobuf standard)
# messages.proto
syntax = "proto3";
message SensorReading {
  uint32 sensor_id = 1;
  int32 temperature = 2;
}

# 2. Generate multi-language code (standard protoc)
protoc --cpp_out=./cpp --java_out=./java messages.proto

# 3. Generate transport adapters (Protocol CodeGen)
protocol-codegen generate-adapter \
  --proto messages.proto \
  --transport sysex \
  --manufacturer-id 0x7D \
  --output-cpp ./cpp/sysex \
  --output-java ./java/sysex

# Result: C++/Java adapter code that wraps protobuf messages in SysEx
```

**Usage in Code:**

```cpp
// C++ (Embedded)
#include "messages.pb.h"
#include "sysex/SysExAdapter.hpp"

SensorReading msg;
msg.set_sensor_id(1);
msg.set_temperature(2350);

uint8_t sysex_buffer[256];
size_t len = SysExAdapter::encode(msg, sysex_buffer);
// Result: F0 7D 42 [protobuf in 7-bit] F7

usbMIDI.sendSysEx(len, sysex_buffer);
```

**Migration Strategy:**

1. **Phase A:** Keep current system working (Python message definitions)
2. **Phase B:** Add protobuf adapter generator as experimental feature
3. **Phase C:** Document migration path for existing users
4. **Phase D:** Deprecate Python message definitions (if protobuf proves better)

**Effort Estimate:** 4-6 weeks for full migration

**Benefits vs Costs:**
- ✅ Much better multi-language support
- ✅ Industry-standard tooling
- ✅ Smaller codebase to maintain
- ✅ Focus on unique value (transport adapters)
- ❌ Breaking change for existing users
- ❌ Dependency on protoc compiler
- ❌ Learning curve for .proto syntax

**Decision:** LOW PRIORITY - Revisit after Phase 1 & 2 complete

**Status:** 💡 Idea / Proposal
**Priority:** P3 (Low)
**Effort:** 4-6 weeks
**Value:** High (long-term)

---

## Community Features (WISHLIST)

### Plugin System
- [ ] Allow users to add custom transport methods
- [ ] Custom type definitions
- [ ] Custom generators

### GUI Tool
- [ ] Visual message designer
- [ ] Real-time code preview
- [ ] Protocol testing/simulation

### Cloud Service
- [ ] Online protocol generator
- [ ] Protocol sharing/marketplace
- [ ] Collaborative editing

**Status:** 💭 Ideas only
**Priority:** P4 (Very Low)

---

## Non-Goals

Things we explicitly don't want to do (at least for now):

❌ **Compete with Protobuf/FlatBuffers** on general-purpose serialization
❌ **Support many languages** (focus: C++, Java, Python only)
❌ **Real-time protocol routing/bridging** (just code generation)
❌ **Hardware-specific features** (keep it generic)
❌ **MIDI 2.0 UMP** (not planned currently)
❌ **Rust, TypeScript, C#** generators (not planned currently)

---

## Version History

**v1.0.0** - Initial extraction from MIDI Studio (current)
**v1.1.0** - Functional standalone package (Phase 1 target)
**v1.2.0** - Tests + examples + PyPI publication (Phase 2 target)
**v2.0.0** - Protobuf integration (future, maybe)

---

## Contributing

Want to help? Check current phase priorities above.

**Phase 1 (now):** Refactoring, testing
**Phase 2 (next):** Examples, documentation
**Phase 3 (later):** Performance, new features

---

Last updated: 2024-11-16
