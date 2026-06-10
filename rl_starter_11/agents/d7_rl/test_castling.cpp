#include "deps/chess.hpp"
#include <iostream>

using namespace chess;

int main() {
    Board board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1");
    Movelist moves;
    movegen::legalmoves(moves, board);
    for (int i = 0; i < moves.size(); i++) {
        Move m = moves[i];
        if (m.typeOf() == Move::CASTLING) {
            std::cout << "Castling move: from=" << m.from() << ", to=" << m.to() << std::endl;
        }
    }
    return 0;
}
