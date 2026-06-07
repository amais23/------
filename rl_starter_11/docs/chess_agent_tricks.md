# 西洋棋 PvP 競賽增強式學習 Agent — 進階優化與黑魔法指南

本文件旨在詳細說明如何在西洋棋 PvP 競賽中，繞過傳統純增強式學習（RL）模型訓練緩慢、易犯低級失誤（如漏看一步殺、自殺步）的缺點，利用 Python 沙箱的特性引入「混合規則引擎」、「棋盤重建」與「搜尋算法」等進階技巧（俗稱黑魔法）來取得壓倒性的優勢。

---

## 目錄
1. [第一部分：在 Agent 中重建 `chess.Board` 狀態](#1-在-agent-中重建-chessboard-狀態)
2. [第二部分：動作編碼與解碼（Action ↔ Move）](#2-動作編碼與解碼action-↔-move)
3. [第三部分：混合規則引擎介入（Rule-Based Overrides）](#3-混合規則引擎介入rule-based-overrides)
4. [第四部分：輕量級 Minimax 與 Alpha-Beta 搜尋](#4-輕量級-minimax-與-alpha-beta-搜尋)
5. [第五部分：`model.zip` 封裝額外資源（Zip 解壓黑魔法）](#5-modelzip-封裝額外資源zip-解壓黑魔法)

---

## 1. 在 Agent 中重建 `chess.Board` 狀態

PettingZoo Chess 傳給 Agent 的觀測值（`observation`）是一個 `(8, 8, 111)` 的 NumPy 陣列。許多同學以為在此維度下只能做卷積神經網路的 Inference，但實際上我們可以直接還原成 `python-chess` 庫中的 `chess.Board` 物件。

由於 PettingZoo 的 Chess 環境始終**以白方視角為基準**（白王初始在下方第 1 列，不隨玩家輪替而翻轉），因此還原映射關係非常固定。

### 重建棋盤程式碼範例

在你的 `agent.py` 中，可以實作以下函數：

```python
import chess
import numpy as np

def reconstruct_board(observation: np.ndarray) -> chess.Board:
    # 建立一個全空的棋盤
    board = chess.Board(None)
    
    # PettingZoo Chess 通道 7 ~ 18 分別對應 12 種棋子
    piece_mapping = {
        7: (chess.PAWN, chess.WHITE),
        8: (chess.KNIGHT, chess.WHITE),
        9: (chess.BISHOP, chess.WHITE),
        10: (chess.ROOK, chess.WHITE),
        11: (chess.QUEEN, chess.WHITE),
        12: (chess.KING, chess.WHITE),
        13: (chess.PAWN, chess.BLACK),
        14: (chess.KNIGHT, chess.BLACK),
        15: (chess.BISHOP, chess.BLACK),
        16: (chess.ROOK, chess.BLACK),
        17: (chess.QUEEN, chess.BLACK),
        18: (chess.KING, chess.BLACK),
    }
    
    # 遍歷通道重建棋子
    for ch, (piece_type, color) in piece_mapping.items():
        channel_slice = observation[:, :, ch]
        for r in range(8):
            for c in range(8):
                if channel_slice[r, c] == 1:
                    # PettingZoo row 0 對應 Rank 8 (上方)，col 0 對應 File A (左邊)
                    # python-chess square 的座標計算：square = file + rank * 8
                    sq = chess.square(c, 7 - r)
                    board.set_piece_at(sq, chess.Piece(piece_type, color))
                    
    # 設定輪到哪一方下子 (通道 4 為 active player 狀態，1 代表白，0 代表黑)
    active_player = observation[0, 0, 4]
    board.turn = chess.WHITE if active_player == 1 else chess.BLACK
    
    # 設定雙方王車易位權限 (通道 0 ~ 3)
    castling_rights = 0
    if observation[0, 0, 1] == 1: castling_rights |= chess.BB_H1  # 白方短易位
    if observation[0, 0, 0] == 1: castling_rights |= chess.BB_A1  # 白方長易位
    if observation[0, 0, 3] == 1: castling_rights |= chess.BB_H8  # 黑方短易位
    if observation[0, 0, 2] == 1: castling_rights |= chess.BB_A8  # 黑方長易位
    board.castling_rights = castling_rights
    
    return board
```

---

## 2. 動作編碼與解碼（Action ↔ Move）

PettingZoo 使用 `Discrete(4672)` 代表動作空間。這是一個扁平化後的 AlphaZero 動作編碼方式（`8 * 8 * 73`，即起點位置乘以 73 種移動方向與升變模式）。

如果我們要讓自訂棋步與環境互動，我們需要進行轉換：

### 使用 `chess_utils` 進行 Move 到 Action 的轉換

```python
from pettingzoo.classic.chess.chess_utils import get_move_plane

def move_to_action(move: chess.Move, board: chess.Board) -> int:
    # 1. 取得起點 square 的座標 (x, y)
    from_square = move.from_square
    x = from_square % 8
    y = from_square // 8
    
    # 2. 調用 PettingZoo 內部函式取得該移動的 move plane (0 ~ 72)
    move_plane = get_move_plane(move)
    
    # 3. 計算扁平化的 action index
    action_index = (y * 8 + x) * 73 + move_plane
    return action_index
```

### 反向轉換：將環境 Action 映射回 `chess.Move` (查表法)

反向轉換（從 `int` 轉回 `chess.Move`）寫解析算法比較繁瑣，在實際對局中，最聰明、最不易出錯的寫法是**「查表法」**：

```python
def get_action_to_move_mapping(board: chess.Board):
    action_to_move = {}
    for move in board.legal_moves:
        action = move_to_action(move, board)
        action_to_move[action] = move
    return action_to_move
```

---

## 3. 混合規則引擎介入（Rule-Based Overrides）

神經網路可能在局部戰術中犯下愚蠢的錯誤（例如明明可以一步將死對手卻去吃小兵，或者漏看己方王被將死的威脅）。我們可以在 `act()` 中加入強制的規則覆寫：

### 規則覆寫實作範例

```python
class Agent:
    def __init__(self):
        # 載入原始 RL 模型...
        pass

    def act(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        # 1. 還原棋盤
        board = reconstruct_board(observation)
        
        # 2. 建立合法動作對照表
        action_to_move = get_action_to_move_mapping(board)
        
        # --- 規則 A：一步殺檢查（Checkmate in 1） ---
        for action, move in action_to_move.items():
            board.push(move)
            is_mate = board.is_checkmate()
            board.pop()
            if is_mate and action_mask[action] == 1:
                return int(action)  # 發現必勝著法，直接回傳！
                
        # --- 規則 B：避開自殺步（Avoid Suicide Moves / Mate in 1） ---
        safe_actions = []
        for action, move in action_to_move.items():
            if action_mask[action] == 0:
                continue
            
            board.push(move)
            # 模擬對手的下一步，看對手能不能在下一手直接將死我們
            opponent_can_mate = False
            for opp_move in board.legal_moves:
                board.push(opp_move)
                if board.is_checkmate():
                    opponent_can_mate = True
                board.pop()
                if opponent_can_mate:
                    break
            board.pop()
            
            if not opponent_can_mate:
                safe_actions.append(action)
                
        # 3. 決策分流
        # 如果有安全的著法，且 RL 預測的著法不安全，就強制從安全著法中用模型預測
        # 如果沒有安全著法，就只能任由 RL 模型決定 (或選隨機)
        
        # 呼叫 RL 模型預測
        obs_flat = observation.flatten().astype(np.float32)
        action_rl, _ = self.model.predict(
            obs_flat,
            action_masks=action_mask.astype(bool),
            deterministic=True,
        )
        action_rl = int(action_rl)
        
        if safe_actions and (action_rl not in safe_actions):
            # RL 預測的棋步會導致我們被一步殺！強迫從安全棋步中選出
            # 這裡可以使用模型對 safe_actions 的機率進行重新評估，或者簡單選擇第一個安全著法
            return int(safe_actions[0])
            
        return action_rl
```

---

## 4. 輕量級 Minimax 與 Alpha-Beta 搜尋

如果你想更進一步，可以直接在 `agent.py` 中寫一個簡單的 Minimax 搜尋引擎。在評測主機 CPU 不錯的狀況下，純 Python 的 2~3 層搜尋能在 **30~100 毫秒**內完成。搭配傳統的子力評估，其實力已遠超隨機或低訓練度的 RL 模型。

### 簡易 Alpha-Beta 搜尋實作

```python
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

def evaluate_board(board: chess.Board) -> int:
    """基礎子力估值函數"""
    if board.is_checkmate():
        return -99999 if board.turn else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
        
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            val = PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                score += val
            else:
                score -= val
    return score

def alpha_beta(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
        
    if maximizing:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            evaluation = alpha_beta(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            evaluation = alpha_beta(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval
```

---

## 5. `model.zip` 封裝額外資源（Zip 解壓黑魔法）

因為平台上傳時限制只能傳 `agent.py`、`model.py` 與 `model.zip`，若是你想在代碼中使用額外的數據（例如：**開局庫**、**殘局表**、**預先計算好的威脅矩陣** 等），你可以**將這些檔案一同打包在 `model.zip` 的壓縮檔中**！

當沙箱在伺服器端載入 `agent.py` 時，我們可以透過 Python 自帶的 `zipfile` 模組在 `__init__` 中將其解壓出來使用。

### 運行時動態解壓範例

在 `agent.py` 中：

```python
import os
import zipfile

class Agent:
    def __init__(self):
        # 1. 取得 model.zip 的絕對路徑
        current_dir = os.path.dirname(__file__)
        zip_path = os.path.join(current_dir, "model.zip")
        extract_dir = os.path.join(current_dir, "extracted_assets")
        
        # 2. 如果尚未解壓過，則在此處動態解壓
        if not os.path.exists(extract_dir) and os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 可以選擇性只解壓我們需要的額外檔案，避免覆蓋 zip 裡的模型權重
                zip_ref.extractall(extract_dir)
                print(f"成功解壓額外資源至: {extract_dir}")
                
        # 3. 讀取你需要的額外資源
        opening_book_path = os.path.join(extract_dir, "my_opening_book.bin")
        if os.path.exists(opening_book_path):
            # 在此載入並應用開局庫...
            pass
            
        # 4. 最後照常載入你的 RL 模型
        self.model = ALGORITHM.load(zip_path, device="cpu")
```

這項技巧可以讓你的 Agent 搭載諸如「Polyglot 開局庫」或「自訂規則 JSON」，大幅提昇實戰的全面性與前期的出子速度。
