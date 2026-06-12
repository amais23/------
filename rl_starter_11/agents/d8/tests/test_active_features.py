import chess

def orient(is_white_pov: bool, sq: int):
    return sq ^ 56 if not is_white_pov else sq

def get_piece_features_detailed(board: chess.Board, is_white_pov: bool):
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    us_indices = []
    print(f"King square (oriented): {king_sq}")
    for sq, p in board.piece_map().items():
        p_idx = (p.piece_type - 1) * 2 + (p.color != is_white_pov)
        oriented_sq = orient(is_white_pov, sq)
        idx = 1 + oriented_sq + p_idx * 64 + king_sq * 769
        print(f"  Piece: {p}, Sq: {chess.square_name(sq)} ({sq}) -> Oriented: {oriented_sq}, p_idx: {p_idx} -> Index: {idx}")
        us_indices.append(idx)
    return us_indices

if __name__ == '__main__':
    print("=== STARTING POSITION ===")
    board_start = chess.Board()
    start_features = get_piece_features_detailed(board_start, True)
    
    print("\n=== LOST POSITION (White down Queen) ===")
    board_lost = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    lost_features = get_piece_features_detailed(board_lost, True)
    
    diff_start_lost = set(start_features) - set(lost_features)
    diff_lost_start = set(lost_features) - set(start_features)
    print(f"\nFeatures in Start but not in Lost: {diff_start_lost}")
    print(f"Features in Lost but not in Start: {diff_lost_start}")
