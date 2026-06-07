#include <iostream>
#include "chess.hpp"

using namespace chess;

int main() {
    Board board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    Move m = uci::uciToMove(board, "e1g1");
    std::cout << "UCI e1g1 -> type: " << (int)m.typeOf() << " from: " << (int)m.from().index() << " to: " << (int)m.to().index() << std::endl;
    return 0;
}
