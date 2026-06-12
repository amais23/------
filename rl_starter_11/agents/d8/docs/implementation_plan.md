# Implementation Plan - Copying d6_cpp to d8 & Integrating Bucket-Based NNUE

This plan outlines copying the `d6_cpp` agent to a new `d8` folder and implementing a high-performance **Bucket-Based NNUE (Efficiently Updatable Neural Network)** evaluation function in C++ using **ARM NEON SIMD** (for macOS M4) and **Intel AVX2 SIMD** (for Linux x86_64), tailored for extreme performance under the 0.5 ~ 1.0 second per move limit.

## User Review Required

> [!IMPORTANT]
> - **Bucket-Based Architecture**: We will replace the legacy `HalfKA` with a modular **Bucket-Based Feature Transformer** (supporting 8, 32, or 64 king buckets). Each bucket maps the absolute coordinates of 11 piece types (5 friendly pieces excluding king + 6 enemy pieces including king) across 64 squares, resulting in 704 features per bucket.
> - **L2 Cache Optimization**: The active weight matrix size is strictly limited to `704 features * 256 L1_SIZE * sizeof(int16_t) = 360 KB` (and ~2.88 MB total for 8 buckets). This guarantees that the active network weights remain permanently resident in the CPU's ultra-fast L2 cache, eliminating cache misses in shared Docker environments.
> - **No GPU Required**: NNUE evaluation runs entirely on the CPU. It is extremely optimized for ARM NEON SIMD (Apple Silicon M4) and Intel AVX2 (Linux) using preprocessor macro conditional compilation.
> - **Embed Weights directly**: To comply with the MLArena submission format (which only allows `agent.py` and `model.zip` / `.so`), we will embed the network weights directly inside the `.so` shared library using the compiler's `.incbin` assembly directive.

## Proposed Changes

### [New Agent Folder: d8]

We will create a new directory `/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8` and copy all source files from `d6_cpp`.

#### [NEW] [nnue_eval.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/nnue_eval.h)
Create a new header file implementing the Bucket-Based NNUE network structure, forward pass, and helper functions:
- **Bucket-Based Feature Transformer**: Maps chess positions to active buckets based on the king's square.
- **Dimensions**: `704 features * 256 L1_SIZE * 2 (perspectives) -> 32 -> 32 -> 1` (quantized network).
- **Alignment**: Ensure all neural network arrays and the accumulator stack are strictly aligned to 32-byte boundaries using `alignas(32)` to prevent segmentation faults when loading AVX2 registers.
- **Conditional SIMD Vectorization**:
  - **ARM NEON (macOS M4)**: Uses ARM NEON intrinsics (`vld1q_s16`, `vaddq_s16`, `vsubq_s16`, and widening vector multiply-accumulate).
  - **Intel AVX2 (Linux x86_64)**: Uses AVX2 intrinsics (`_mm256_add_epi16`, `_mm256_sub_epi16`, `_mm256_maddubs_epi16`, and `_mm256_madd_epi16` for fast 8-bit dot products).
  - **Scalar Fallback**: Clean loop-based fallback for compilers/platforms without SIMD support.

#### [NEW] [weights.S](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights.S)
Create an assembly file to embed `nn.nnue` directly into the binary using the `.incbin` directive. It will export `nn_nnue` and `nn_nnue_len` symbols:
- **OS Compatibility & Underscore Detection**: Use macros to distinguish between macOS (Mach-O, which requires a leading underscore like `_nn_nnue`) and Linux (ELF, which expects no prefix like `nn_nnue`), ensuring perfect compatibility when compiled inside Docker `manylinux`.
- **Automatic Size Calculation**: Calculate size automatically using symbol arithmetic (e.g., `_nn_nnue_end - _nn_nnue`).

#### [MODIFY] [setup.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/setup.py)
Update build extension to compile `weights.S` alongside `engine.cpp` and name the module `chess_engine_d8_han`.

#### [MODIFY] [agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/agent.py)
- Rename imported module `chess_engine_d6_han` to `chess_engine_d8_han`.
- Keep the `model.zip` dynamic loading bootloader intact.

#### [MODIFY] [engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/engine.cpp)
Integrate incremental accumulator updates and NNUE evaluation:
- Declare `alignas(32) std::array<int16_t, L1_SIZE> m_accumulator_stack_w[128]` and `m_accumulator_stack_b[128]` inside `SearchEngine`.
- Initialize accumulators from scratch at the root of `search_best_move`.
- **Incremental Same-Bucket King Moves**: When the king moves within the same bucket boundaries, keep updates purely incremental ($O(1)$ complexity, only updating the king's features) instead of recalculating the entire board.
- **Cross-Bucket King Moves**: Only trigger a full accumulator recalculation when the king crosses bucket boundaries or when castling occurs.
- Update `alpha_beta` and `quiescence` signatures to pass the current search `ply`.

#### [MODIFY] [build.sh](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/build.sh) / [pack.sh](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/pack.sh)
Modify files to target the `d8` folder and build/rename `chess_engine_d8_han` assets correctly.

## Verification Plan

### Automated Tests
- Copy `nn-8a08400ed089.nnue` from the scratch directory to `/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/nn.nnue`.
- Run `./build.sh` to compile the macOS shared library.
- Create and run `test_nnue.py` in `d8` to verify:
  1. The NNUE weights load successfully.
  2. The evaluation outputs are deterministic, symmetric, and reasonable (e.g. starting position evaluation is close to +15cp to +25cp for White).
  3. Incremental accumulator updates produce the exact same values as full recalculations.
- Run `tournament.py` locally to pit the new `d8` agent against the baseline `d6_cpp` agent to verify Elo improvement (target: +200 Elo).
