import chess
from tests.test_cpp_vs_python import get_piece_features, get_enemy_features, orient

def inspect():
    board = chess.Board()
    print("=== Start Position Us Features ===")
    us_start = get_piece_features(board, True)
    for sq, p in board.piece_map().items():
        oriented_sq = orient(True, sq)
        p_idx = (p.piece_type - 1) * 2 + (p.color != True)
        idx = 1 + oriented_sq + p_idx * 64 + 4 * 769
        print(f"Piece: {p} at {chess.square_name(sq)} (oriented: {oriented_sq}), p_idx: {p_idx}, idx: {idx}")

    print("\n=== Start Position Enemy Features ===")
    enemy_start = get_enemy_features(board, True)
    for sq, p in board.piece_map().items():
        if p.piece_type == chess.KING and p.color == True:
            continue
        oriented_sq = orient(False, sq)
        if p.piece_type == chess.PAWN:
            pawn_plane = 0 if p.color == False else 1
            plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
        else:
            pt_idx = (p.piece_type - 2) * 2 + (p.color != False)
            plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
        idx = plane_offset + 4 * 685
        print(f"Piece: {p} at {chess.square_name(sq)} (oriented: {oriented_sq}), plane_offset: {plane_offset}, idx: {idx}")

if __name__ == '__main__':
    inspect()
