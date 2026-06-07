#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Arena — Chess Agent Multi-slot Upload Script
Usage:
  python run.py --slot 0   # Upload Hybrid RL Agent (PPO + Safety Net)
  python run.py --slot 1   # Upload Alpha-Beta Search Agent (Depth 3)
  python run.py --slot 2   # Upload Deep Alpha-Beta Search Agent (Depth 4)
"""

import os
import sys
import shutil
import argparse
from arena_client import MLArenaClient



def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Upload Agent to MLArena slot.")
    parser.add_argument("--slot", type=int, default=0, choices=[0, 1, 2], help="Slot index (0, 1, or 2)")
    parser.add_argument("--agent_type", type=str, default="d5_pro", help="Directory name under agents/ to upload (e.g., rl, d3, d4_pro, d5_pro)")
    parser.add_argument("--upload", action="store_true", help="Upload flag (kept for compatibility)")
    args = parser.parse_args()

    STUDENT_ID     = "41241213S"
    COMPETITION_ID = 11
    SLOT_INDEX     = args.slot
    AGENT_TYPE     = args.agent_type

    # Define metadata based on agent_type
    if AGENT_TYPE == "d6_cpp":
        SLOT_NAME = "D6 Engine"
        DESCRIPTION = "D6 Ported Search Engine (Depth 8-10, TT, LMR, Polyglot Book, Syzygy)"
    elif AGENT_TYPE == "d5_pro":
        SLOT_NAME = "D5 Pro"
        DESCRIPTION = "D5 Pro (Parallel Alpha-Beta + Fallback)"
    elif AGENT_TYPE == "d4_pro":
        SLOT_NAME = "D4 Pro v2"
        DESCRIPTION = "D4 Pro v2 (Single-thread Alpha-Beta)"
    elif AGENT_TYPE == "rl":
        SLOT_NAME = "RL Agent"
        DESCRIPTION = "Hybrid RL Agent (PPO)"
    elif AGENT_TYPE == "d3":
        SLOT_NAME = "D3"
        DESCRIPTION = "Alpha-Beta Depth 3"
    else:
        SLOT_NAME = AGENT_TYPE.upper()
        DESCRIPTION = f"{AGENT_TYPE} Agent"

    print("=" * 60)
    print(f"準備上傳槽位 #{SLOT_INDEX}...")
    print(f"目標 Agent: {AGENT_TYPE}")
    print(f"顯示名稱: {SLOT_NAME}")
    print(f"描述: {DESCRIPTION}")
    print("=" * 60)

    # Verify source directory exists
    agent_dir = f"agents/{AGENT_TYPE}"
    
    if not os.path.exists(agent_dir):
        print(f"❌ 錯誤: 找不到目錄 {agent_dir}！請確認它存在。")
        return

    agent_file = os.path.join(agent_dir, "agent.py")
    model_file = os.path.join(agent_dir, "model.py")
    weights_file = os.path.join(agent_dir, "model.zip")
    if not os.path.exists(weights_file):
        weights_file = "model.zip" if os.path.exists("model.zip") else None

    client = MLArenaClient(student_id=STUDENT_ID)
    if not client.api_key:
        print(f"首次執行，正在以學號 {STUDENT_ID} 領取帳號...")
        try:
            client.enroll(student_id=STUDENT_ID)
        except RuntimeError as e:
            print("-" * 50)
            print(f"帳號領取失敗：{e}")
            print("-" * 50)
            return


    if weights_file is None and SLOT_INDEX == 0:
        print("⚠️ 警告: 找不到 model.zip，上傳 RL 槽位但無模型權重！請確認是否需要先進行訓練。")

    print(f"正在上傳 Agent 至槽位 #{SLOT_INDEX}...")
    try:
        client.upload_rl_slot(
            competition_id=COMPETITION_ID,
            slot_index=SLOT_INDEX,
            agent_file=agent_file,
            model_file=model_file,
            weights_file=weights_file,
            name=SLOT_NAME,
            description=DESCRIPTION,
        )
        print(f"🎉 槽位 #{SLOT_INDEX} 上傳成功！")
    except RuntimeError as e:
        print(f"❌ 上傳失敗：{e}")
        return

    print("\n目前槽位狀態：")
    client.list_rl_slots(COMPETITION_ID)

if __name__ == "__main__":
    main()
