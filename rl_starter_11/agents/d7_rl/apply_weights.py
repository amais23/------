import numpy as np

def update_engine():
    # Load optimized weights
    w = np.load("FEN_data/optimized_weights.npy")
    
    # Calculate scale factor to keep Pawn at exactly 100
    scale = 100.0 / w[0]
    scaled_w = w * scale
    
    # 459 dimensions map:
    # [0..4]   : Piece Values (P, N, B, R, Q) -> 5 params
    # [5..68]  : PST_PAWN -> 64 params
    # [69..132]: PST_KNIGHT -> 64 params
    # [133..196]: PST_BISHOP -> 64 params
    # [197..260]: PST_ROOK -> 64 params
    # [261..324]: PST_QUEEN -> 64 params
    # [325..388]: PST_KING_MID -> 64 params
    # [389..452]: PST_KING_END -> 64 params
    # [453]    : Bishop Pair -> 1 param
    # [454]    : King Castled -> 1 param
    # [455]    : Rook Open File -> 1 param
    # [456]    : Passed Pawn -> 1 param
    # [457]    : Doubled Pawn -> 1 param
    # [458]    : Isolated Pawn -> 1 param

    piece_values = np.round(scaled_w[0:5]).astype(int)
    # C++ PIECE_VAL: {P, N, B, R, Q, K, NONE}
    # Original: {100, 320, 330, 500, 900, 20000, 0}
    piece_val_str = f"static constexpr int PIECE_VAL[7] = {{{piece_values[0]}, {piece_values[1]}, {piece_values[2]}, {piece_values[3]}, {piece_values[4]}, 20000, 0}};"

    def fmt_array(arr, name):
        rounded = np.round(arr).astype(int)
        lines = []
        for i in range(0, len(rounded), 16):
            chunk = rounded[i:i+16]
            chunk_str = ", ".join(map(str, chunk))
            lines.append("    " + chunk_str)
        inner = ",\n".join(lines)
        return f"static constexpr int16_t {name}[64] = {{\n{inner}}};"

    pst_pawn_str = fmt_array(scaled_w[5:69], "PST_PAWN")
    pst_knight_str = fmt_array(scaled_w[69:133], "PST_KNIGHT")
    pst_bishop_str = fmt_array(scaled_w[133:197], "PST_BISHOP")
    pst_rook_str = fmt_array(scaled_w[197:261], "PST_ROOK")
    pst_queen_str = fmt_array(scaled_w[261:325], "PST_QUEEN")
    pst_king_mid_str = fmt_array(scaled_w[325:389], "PST_KING_MID")
    pst_king_end_str = fmt_array(scaled_w[389:453], "PST_KING_END")

    # Extra terms:
    # Note: original code hardcoded adjustments:
    # Bishop pair: score += 50 (w[453] = -22.22 * 4.029 = -89.5 -> -90)
    # King Castled: score += 30 (w[454] = -38.06 * 4.029 = -153.3 -> -153)
    # Rook Open File: score += 20 (w[455] = -15.26 * 4.029 = -61.5 -> -61)
    # Passed Pawn: score += 10 * rank (w[456] = 5.43 * 4.029 = 21.87 -> 22)
    # Doubled Pawn: score -= 10 * count (w[457] = -1.86 * 4.029 = -7.5 -> -8) -> in C++, score -= coeff * (count - 1), so coeff = -round(w[457])
    # Isolated Pawn: score -= 15 (w[458] = -8.17 * 4.029 = -32.9 -> -33) -> in C++, score -= coeff, so coeff = -round(w[458])
    
    bp_val = int(round(scaled_w[453]))
    kc_val = int(round(scaled_w[454]))
    ro_val = int(round(scaled_w[455]))
    pp_val = int(round(scaled_w[456]))
    dp_val = int(round(scaled_w[457]))
    ip_val = int(round(scaled_w[458]))

    print("--- Tuned Parameters ---")
    print(piece_val_str)
    print("Bishop Pair:", bp_val)
    print("King Castled:", kc_val)
    print("Rook Open File:", ro_val)
    print("Passed Pawn Multiplier:", pp_val)
    print("Doubled Pawn Penalty (raw):", dp_val)
    print("Isolated Pawn Penalty (raw):", ip_val)

    # Read original engine.cpp
    with open("engine.cpp", "r") as f:
        content = f.read()

    # Find the target block for PIECE_VAL and PSTs
    import re
    pattern = r"static constexpr int PIECE_VAL\[7\].*?static constexpr int16_t PST_KING_END\[64\].*?};"
    
    new_block = "\n".join([
        piece_val_str, "",
        pst_pawn_str, "",
        pst_knight_str, "",
        pst_bishop_str, "",
        pst_rook_str, "",
        pst_queen_str, "",
        pst_king_mid_str, "",
        pst_king_end_str
    ])

    # Let's do a direct replacement in content
    # We can locate where it starts and ends
    start_idx = content.find("static constexpr int PIECE_VAL[7]")
    end_idx = content.find("};", content.find("static constexpr int16_t PST_KING_END[64]"))
    if start_idx == -1 or end_idx == -1:
        print("Could not find the target constants in engine.cpp")
        return
    
    end_idx += 2 # include };
    old_block = content[start_idx:end_idx]
    
    content = content.replace(old_block, new_block)

    # Now let's update the evaluation function extra terms:
    # 1. Bishop Pair: original: score += 50 / score -= 50
    # Bishop Pair in features is w[453] = 1.0 (for white having pair). 
    # Scaled w[453] is -90. If w[453] is negative, that means white bishop pair gets a penalty, or we should use + bp_val directly. Let's do `score += bp_val` (since bp_val is signed).
    # Wait, in features: if board.pieces(PieceType::BISHOP, Color::WHITE).count() == 2: ptr[453] += 1.0f
    # So if bp_val is -90, it means white bishop pair gets -90! Let's update `score += bp_val` and `score -= bp_val` accordingly.
    # Let's inspect the original code:
    #     if (board.pieces(PieceType::BISHOP, Color::WHITE).count() == 2)
    #       score += 50;
    #     if (board.pieces(PieceType::BISHOP, Color::BLACK).count() == 2)
    #       score -= 50;
    # We replace 50 with bp_val (or if bp_val is negative, we should keep the same pattern score += bp_val and score -= bp_val, which handles signs automatically!).
    # Wait, if bp_val is -90, white having bishop pair adds -90 to score, black having bishop pair subtracts -90 (adds +90).
    # Since features extractor has: if (white has 2) ptr[453] += 1; if (black has 2) ptr[453] -= 1;
    # Then prediction is Score = X * W. So white having 2 bishops contributes +1.0 * w[453] to the score.
    # Therefore, the score adjustment in the engine should be:
    # score += bp_val for white, score -= bp_val for black.
    
    # 2. King Castled:
    # original: 
    #     Square ksq_w = board.kingSq(Color::WHITE);
    #     if (ksq_w == Square("c1") || ksq_w == Square("g1") || ksq_w == Square("b1"))
    #       score += 30;
    #     Square ksq_b = board.kingSq(Color::BLACK);
    #     if (ksq_b == Square("c8") || ksq_b == Square("g8") || ksq_b == Square("b8"))
    #       score -= 30;
    # We replace 30 with kc_val.
    
    # 3. Rook on open/half-open files:
    # original: score += 20 / score -= 20
    # We replace 20 with ro_val.
    
    # 4. Passed Pawns:
    # original: score += 10 * (sq.index() / 8); / score -= 10 * (7 - (sq.index() / 8));
    # We replace 10 with pp_val.
    
    # 5. Doubled pawns:
    # original:
    #       if (count_w > 1) {
    #         score -= 10 * (count_w - 1);
    #       }
    #       ...
    #       if (count_b > 1) {
    #         score += 10 * (count_b - 1);
    #       }
    # In features extractor:
    #         int count_w = (pawns_w_bits & file_mask) ? Bitboard(pawns_w_bits & file_mask).count() : 0;
    #         if (count_w > 1) ptr[457] += (count_w - 1);
    #         int count_b = (pawns_b_bits & file_mask) ? Bitboard(pawns_b_bits & file_mask).count() : 0;
    #         if (count_b > 1) ptr[457] -= (count_b - 1);
    # So white doubled pawn adds (count_w - 1) * w[457] to score.
    # Therefore, score += dp_val * (count_w - 1) for white, score -= dp_val * (count_b - 1) for black.
    # Since dp_val is -8, this is equivalent to: score += (-8) * (count_w - 1) = score -= 8 * (count_w - 1).
    # Thus:
    #       if (count_w > 1) {
    #         score += dp_val * (count_w - 1);
    #       }
    #       ...
    #       if (count_b > 1) {
    #         score -= dp_val * (count_b - 1);
    #       }
    
    # 6. Isolated pawns:
    # original: score -= 15 / score += 15
    # features:
    #         if ((pawns_w_bits & file_mask) && !(pawns_w_bits & adj_mask)) ptr[458] += 1.0f;
    #         if ((pawns_b_bits & file_mask) && !(pawns_b_bits & adj_mask)) ptr[458] -= 1.0f;
    # White isolated pawn adds 1.0 * w[458] = ip_val to score.
    # So: score += ip_val for white isolated pawn, score -= ip_val for black isolated pawn.
    # Since ip_val is -33, score += (-33) = score -= 33.
    # So we replace 15 with -ip_val (which is +33, so score -= 33 / score += 33).
    # Or just replace the score adjustments with:
    #       if ((pawns_w_bits_v & file_mask) && !(pawns_w_bits_v & adj_mask)) {
    #         score += ip_val;
    #       }
    #       if ((pawns_b_bits_v & file_mask) && !(pawns_b_bits_v & adj_mask)) {
    #         score -= ip_val;
    #       }

    # Let's perform replacements in the code:
    # Bishop Pair replacement:
    content = content.replace(
        "    if (board.pieces(PieceType::BISHOP, Color::WHITE).count() == 2)\n      score += 50;\n    if (board.pieces(PieceType::BISHOP, Color::BLACK).count() == 2)\n      score -= 50;",
        f"    if (board.pieces(PieceType::BISHOP, Color::WHITE).count() == 2)\n      score += {bp_val};\n    if (board.pieces(PieceType::BISHOP, Color::BLACK).count() == 2)\n      score -= {bp_val};"
    )
    
    # King Castled replacement:
    content = content.replace(
        '    Square ksq_w = board.kingSq(Color::WHITE);\n    if (ksq_w == Square("c1") || ksq_w == Square("g1") || ksq_w == Square("b1"))\n      score += 30;\n\n    Square ksq_b = board.kingSq(Color::BLACK);\n    if (ksq_b == Square("c8") || ksq_b == Square("g8") || ksq_b == Square("b8"))\n      score -= 30;',
        f'    Square ksq_w = board.kingSq(Color::WHITE);\n    if (ksq_w == Square("c1") || ksq_w == Square("g1") || ksq_w == Square("b1"))\n      score += {kc_val};\n\n    Square ksq_b = board.kingSq(Color::BLACK);\n    if (ksq_b == Square("c8") || ksq_b == Square("g8") || ksq_b == Square("b8"))\n      score -= {kc_val};'
    )
    
    # Rooks Open File replacement:
    content = content.replace(
        "      if (!(board.pieces(PieceType::PAWN, Color::WHITE).getBits() & file_mask)) {\n        score += 20;\n      }",
        f"      if (!(board.pieces(PieceType::PAWN, Color::WHITE).getBits() & file_mask)) {{\n        score += {ro_val};\n      }}"
    )
    content = content.replace(
        "      if (!(board.pieces(PieceType::PAWN, Color::BLACK).getBits() & file_mask)) {\n        score -= 20;\n      }",
        f"      if (!(board.pieces(PieceType::PAWN, Color::BLACK).getBits() & file_mask)) {{\n        score -= {ro_val};\n      }}"
    )
    
    # Passed Pawns replacement:
    content = content.replace(
        "      if (!(pawns_b_bits_v & m_passed_pawn_masks[0][sq.index()])) {\n        score += 10 * (sq.index() / 8);\n      }",
        f"      if (!(pawns_b_bits_v & m_passed_pawn_masks[0][sq.index()])) {{\n        score += {pp_val} * (sq.index() / 8);\n      }}"
    )
    content = content.replace(
        "      if (!(pawns_w_bits_v & m_passed_pawn_masks[1][sq.index()])) {\n        score -= 10 * (7 - (sq.index() / 8));\n      }",
        f"      if (!(pawns_w_bits_v & m_passed_pawn_masks[1][sq.index()])) {{\n        score -= {pp_val} * (7 - (sq.index() / 8));\n      }}"
    )

    # Doubled & Isolated Pawns replacement:
    # Original:
    #       int count_w = (pawns_w_bits_v & file_mask) ? Bitboard(pawns_w_bits_v & file_mask).count() : 0;
    #       if (count_w > 1) {
    #         score -= 10 * (count_w - 1);
    #       }
    #       int count_b = (pawns_b_bits_v & file_mask) ? Bitboard(pawns_b_bits_v & file_mask).count() : 0;
    #       if (count_b > 1) {
    #         score += 10 * (count_b - 1);
    #       }
    # 
    #       // Isolated pawns
    #       if ((pawns_w_bits_v & file_mask) && !(pawns_w_bits_v & adj_mask)) {
    #         score -= 15;
    #       }
    #       if ((pawns_b_bits_v & file_mask) && !(pawns_b_bits_v & adj_mask)) {
    #         score += 15;
    #       }
    old_pawn_structure = """      // Doubled pawns
      int count_w = (pawns_w_bits_v & file_mask) ? Bitboard(pawns_w_bits_v & file_mask).count() : 0;
      if (count_w > 1) {
        score -= 10 * (count_w - 1);
      }
      int count_b = (pawns_b_bits_v & file_mask) ? Bitboard(pawns_b_bits_v & file_mask).count() : 0;
      if (count_b > 1) {
        score += 10 * (count_b - 1);
      }

      // Isolated pawns
      if ((pawns_w_bits_v & file_mask) && !(pawns_w_bits_v & adj_mask)) {
        score -= 15;
      }
      if ((pawns_b_bits_v & file_mask) && !(pawns_b_bits_v & adj_mask)) {
        score += 15;
      }"""

    new_pawn_structure = f"""      // Doubled pawns
      int count_w = (pawns_w_bits_v & file_mask) ? Bitboard(pawns_w_bits_v & file_mask).count() : 0;
      if (count_w > 1) {{
        score += {dp_val} * (count_w - 1);
      }}
      int count_b = (pawns_b_bits_v & file_mask) ? Bitboard(pawns_b_bits_v & file_mask).count() : 0;
      if (count_b > 1) {{
        score -= {dp_val} * (count_b - 1);
      }}

      // Isolated pawns
      if ((pawns_w_bits_v & file_mask) && !(pawns_w_bits_v & adj_mask)) {{
        score += {ip_val};
      }}
      if ((pawns_b_bits_v & file_mask) && !(pawns_b_bits_v & adj_mask)) {{
        score -= {ip_val};
      }}"""

    content = content.replace(old_pawn_structure, new_pawn_structure)

    with open("engine.cpp", "w") as f:
        f.write(content)
    
    print("engine.cpp has been successfully updated with tuned parameters!")

if __name__ == "__main__":
    update_engine()
