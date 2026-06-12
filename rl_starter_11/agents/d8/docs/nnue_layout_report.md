# NNUE Weight Layout & Reverse Engineering Report

This document details the exact layout, parameter structures, feature mapping, and forward pass mathematics of the `nn.nnue` neural network weights verified in the `d8` folder.

---

## 1. Network Overview

The network is defined by the following signature inside the file header:
*   **Version**: `0x7af32f20`
*   **Network Hash**: `0x3c103e72`
*   **Description**:
    `Features=HalfKA(Friend)[49216->256x2],Network=AffineTransform[1<-32](ClippedReLU[32](AffineTransform[32<-32](ClippedReLU[32](AffineTransform[32<-512](InputSlice[512(0:512)])))))`

---

## 2. Embedded Weight Layout

The file `nn.nnue` has a total size of `47,721,473` bytes. The byte offsets are mapped exactly as follows:

| Section | Absolute Start Byte | Size (Bytes) | Description |
| :--- | :--- | :--- | :--- |
| **Header** | `0` | `189` | Version, hash, and description string. |
| **FT Hash** | `189` | `4` | Feature Transformer hash `0x5f2348b8`. |
| **Friend FT Bias** | `193` | `512` | 256 `int16_t` values. |
| **Friend FT Weights** | `705` | `25,198,592` | $49,216 \times 256$ `int16_t` values. |
| **Enemy FT Bias** | `25,199,297` | `512` | 256 `int16_t` values. |
| **Enemy FT Weights** | `25,199,809` | `22,446,080` | $43,840 \times 256$ `int16_t` values. |
| **FC Section Hash** | `47,645,889` | `4` | Initial `fc_hash` or metadata start. |
| **FC Metadata** | `47,645,893` | `268` | Layer configuration metadata. |
| **Isolated Buckets 0-3** | `47,646,161` | `4,768` | $4 \times 1,192$-byte stacks (L2+L3 only). |
| **Main Stacks 0-3** | `47,650,913` | `70,560` | $4 \times 17,640$-byte stacks (L1+L2+L3). |

---

## 3. Feature Transformer Mapping

### 3.1 Friend PoV (Us) — 49,216 Features
*   **Planes**: 769 planes ($12 \text{ piece types} \times 64 \text{ squares} + 1$).
*   **Piece Type Ordering**: Pawn=1, Knight=2, Bishop=3, Rook=4, Queen=5, King=6.
*   **Index Calculation**:
    $$p\_idx = (\text{piece\_type} - 1) \times 2 + (\text{color} \neq \text{side\_to\_move})$$
    $$\text{idx} = 1 + \text{orient}(\text{side\_to\_move}, \text{square}) + p\_idx \times 64 + \text{orient}(\text{side\_to\_move}, \text{king\_square}) \times 769$$
    *   $\text{orient}(\text{pov}, \text{sq})$ returns $\text{sq}$ if pov is White, and $\text{sq} \oplus 56$ (vertical flip) if pov is Black.

### 3.2 Enemy PoV (Them) — 43,840 Features
*   **Planes**: 685 planes.
*   **Index Calculation**:
    *   The opponent's king (Us King from Them PoV) is **excluded** from the features list.
    *   Pawns are mapped to a **48-square plane** (ranks 2-7, squares 8 to 55).
    *   If the piece is a Pawn:
        $$\text{pawn\_plane} = 0 \text{ (own Pawn)} \text{ or } 1 \text{ (enemy Pawn) from Them PoV}$$
        $$\text{plane\_offset} = 1 + \text{pawn\_plane} \times 48 + (\text{orient}(\text{them\_pov}, \text{square}) - 8)$$
    *   If the piece is any other type (Knight, Bishop, Rook, Queen, own King):
        $$pt\_idx = (\text{piece\_type} - 2) \times 2 + (\text{color} \neq \text{them\_pov})$$
        $$\text{plane\_offset} = 1 + 96 + pt\_idx \times 64 + \text{orient}(\text{them\_pov}, \text{square})$$
    *   The final Enemy index is:
        $$\text{idx} = \text{plane\_offset} + \text{orient}(\text{them\_pov}, \text{them\_king\_square}) \times 685$$

---

## 4. Fully-Connected Layers & Bucket Architecture

### 4.1 King Bucket Mapping
The board uses an 8-bucket division of king squares. The bucket index is mapped relative to the oriented king square $S$:
$$i = 7 - (S / 8) \in [0, 7]$$

*   **Buckets 0-2 (Ranks 6, 7, 8)**: Contain initial/untrained garbage values due to lack of visits in gameplay.
*   **Bucket 3 (Rank 5)**: Contains trained values (Isolated Bucket 3).
*   **Buckets 4-7 (Ranks 1, 2, 3, 4)**: Contain trained/clean values (Main Stacks 0-3).

### 4.2 Parameter Loading & Mapping
For a given king bucket $i$:
1.  **L1 Layer** (16 outputs, 1024 inputs):
    *   We always use the L1 parameters from **Main Stack** $k = i \pmod 4$.
2.  **L2 & L3 Layers**:
    *   If $i < 4$ (Buckets 0-3): L2+L3 are loaded from **Isolated Bucket** $i$.
    *   If $i \ge 4$ (Buckets 4-7): L2+L3 are loaded from **Main Stack** $i - 4$.

---

## 5. Forward Pass Mathematics

1.  **Feature Accumulators**:
    $$A_{us} = \text{friend\_bias} + \sum \text{friend\_weights}[idx_{us}] \pmod{2^{16}}$$
    $$A_{them} = \text{enemy\_bias} + \sum \text{enemy\_weights}[idx_{them}] \pmod{2^{16}}$$
2.  **Accumulator Activation (Dual-sided Clipped ReLU)**:
    Scale down by 127, then separate positive and negative parts to form a 1024-dimensional vector:
    $$f_{dual}(A) = [\min(\max(0, A / 127), 127), \min(\max(0, -A / 127), 127)]$$
    $$I_{L1} = [f_{dual}(A_{us}), f_{dual}(A_{them})]$$
3.  **L1 Propagation**:
    $$O_{L1} = I_{L1} \cdot W_{L1} + B_{L1} \quad (\text{dimension: } 16)$$
4.  **L1 Activation (Dual-sided Clipped ReLU)**:
    Scale down by 64, then separate positive and negative parts to form a 32-dimensional vector:
    $$I_{L2} = f_{dual}(O_{L1} / 64)$$
5.  **L2 Propagation**:
    $$O_{L2} = I_{L2} \cdot W_{L2} + B_{L2} \quad (\text{dimension: } 32)$$
6.  **L2 Activation (Standard Clipped ReLU)**:
    $$I_{L3} = \min(\max(0, O_{L2} / 64), 127) \quad (\text{dimension: } 32)$$
7.  **L3 Propagation**:
    $$O_{L3} = I_{L3} \cdot W_{L3} + B_{L3} \quad (\text{dimension: } 1)$$
8.  **Output Conversion**:
    To convert the raw score to centipawns:
    $$\text{score\_in\_cp} = O_{L3} / 100$$

---

## 6. Starting Position Verification Results

Evaluating the starting position FEN using this exact math yields:
*   **Raw Output**: `1911`
*   **Centipawn Score**: `+19.11 cp` (which is within the expected range of `+15cp to +25cp` for White's starting position).
