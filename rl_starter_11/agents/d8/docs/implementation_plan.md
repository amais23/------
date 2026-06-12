# Implementation Plan - Copying d6_cpp to d8 & Integrating Bucket-Based NNUE

This plan outlines copying the `d6_cpp` agent to a new `d8` folder and implementing a high-performance **Bucket-Based NNUE (Efficiently Updatable Neural Network)** evaluation function in C++ using **ARM NEON SIMD** (for macOS M4) and **Intel AVX2 SIMD** (for Linux x86_64), tailored for extreme performance under the 0.5 ~ 1.0 second per move limit.

## User Review Required

> [!IMPORTANT]
> - **Bucket-Based Architecture**:
>   - **Feature Transformers**: Us (Friend FT) has 49,216 inputs to 256 outputs; Them (Enemy FT) has 43,840 inputs to 256 outputs.
>   - **Fully-Connected (FC) layers**: The network has 8 buckets. Buckets 0-3 (isolated buckets) bypass L1 (only L2+L3 are stored, size 1192 bytes each). Buckets 4-7 (main stacks) include L1, L2, and L3 (size 17,640 bytes each).
>   - **King Bucket Mapping**: We map oriented King square $S$ to bucket $i = 7 - (S / 8) \in [0, 7]$.
>     - If $i < 4$, we use L1 bucket $k = i$ (Main Stack $i$) and L2+L3 from Isolated Bucket $i$.
>     - If $i \ge 4$, we use L1 bucket $k = i - 4$ (Main Stack $i - 4$) and L2+L3 from Main Stack $i - 4$.
> - **L2 Cache Optimization**: The network size is kept extremely compact, assuring that the active weights remain permanently resident in CPU L2 cache for instant retrieval.
> - **Direct Weight Embedding**: We embed `nn.nnue` (total size 47,721,473 bytes) directly into the compiled library using the compiler's `.incbin` directive in assembly, supporting both Mach-O (macOS) and ELF (Linux) formats.

## Proposed Changes

### [New Agent Folder: d8]

We will copy all files from `d6_cpp` into a new directory `/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8` and perform modifications.

#### [NEW] [nnue_eval.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/nnue_eval.h)
Create a C++ header containing:
- **Struct definitions**: Representing mapped pointers to the raw memory of the embedded `nn.nnue` weights/biases.
- **Index mapping functions**:
  - `friend_idx`: Maps piece types and squares relative to own king PoV starting at index 1.
  - `enemy_idx`: Maps piece types and squares relative to enemy king PoV starting at index 1, excluding opponent's king (Us King from Them PoV) and mapping Pawns to a 48-square plane (ranks 2-7).
- **Forward Pass**:
  - Incremental accumulator update using `accum_add` and `accum_sub`.
  - Dual-sided Clipped ReLU for Us (256 $\to$ 512) and Them (256 $\to$ 512), concatenating to 1024 input elements.
  - L1 linear dot product ($16 \times 1024$) and bias addition.
  - Dual-sided Clipped ReLU on L1 output ($16 \to 32$).
  - L2 linear ($32 \times 32$) and bias addition.
  - Standard Clipped ReLU ($32 \to 32$).
  - L3 linear ($1 \times 32$) and bias addition.
- **SIMD Implementations**:
  - **ARM NEON**: Widening vector operations to process 8 `int16_t` and 16 `int8_t` elements in parallel.
  - **Intel AVX2**: `_mm256_add_epi16`, `_mm256_sub_epi16`, and `_mm256_maddubs_epi16` for extremely fast 8-bit dot products.
  - **Scalar Fallback**: Clean loop-based code for platforms without SIMD.

#### [MODIFY] [setup.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/setup.py)
Update build extension to compile `src/weights.S` alongside `src/engine.cpp` and name the module `chess_engine_d8_han`.

#### [MODIFY] [agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/agent.py)
Rename imported module from `chess_engine_d6_han` to `chess_engine_d8_han`.

#### [MODIFY] [engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/engine.cpp)
Integrate incremental accumulator updates and NNUE evaluation:
- Keep the `alignas(32) std::array<int16_t, 256>` accumulator stack.
- Handle incremental accumulator updates on regular piece moves.
- Recalculate accumulators from scratch only on king moves or castling.
- Replace classical evaluation with `nnue_eval` normalized to centipawns by dividing raw score by 100.

#### [MODIFY] [build.sh](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/build.sh) / [pack.sh](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/pack.sh)
Update targets to build `chess_engine_d8_han` assets.

---

## Verification Plan

### Automated Tests
- Run `./build.sh` using the root virtual environment `/Users/Shared/西洋棋代理人/.venv/bin/python3`.
- Write `test_debug_fen_precise.py` in `d8` to compare C++ evaluations against the verified Python outputs (starting position raw score ~1900-2100).
- Assert that incremental updates produce the exact same activations as full recalculations.
- Run `tournament.py` to pit `d8` against `d6_cpp` and verify Elo progress (target: +200 Elo).
