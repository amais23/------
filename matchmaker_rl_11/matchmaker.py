#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Arena Chess RL Matchmaking Automator with ELO & CSV Log Monitoring
Author: Antigravity AI
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
from datetime import datetime

API_BASE = "https://api-mlarena.spkuan.cc/api"
COMPETITION_ID = 11
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ANSI color codes for pretty terminal logs
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Regular expression to strip ANSI codes from string
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def log(message, color=RESET, write_file=True):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # 1. Print color-coded message in terminal
    print(f"[{timestamp}] {color}{message}{RESET}")
    
    # 2. Append to matchmaker.log without ANSI codes
    if write_file:
        try:
            clean_msg = ANSI_ESCAPE.sub('', formatted_message)
            with open("matchmaker.log", "a", encoding="utf-8") as f:
                f.write(clean_msg + "\n")
        except Exception:
            pass

def log_match_csv(battle_id, opponent, opponent_elo, result, elo_before, elo_after, elo_change):
    csv_file = "match_history.csv"
    file_exists = os.path.exists(csv_file)
    try:
        with open(csv_file, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("Timestamp,Battle_ID,Opponent,Opponent_Elo,Result,Elo_Before,Elo_After,Elo_Change\n")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Enclose values in quotes to prevent formatting issues
            f.write(f'"{timestamp}",{battle_id},"{opponent}",{opponent_elo:.2f},"{result}",{elo_before:.2f},{elo_after:.2f},{elo_change:+.2f}\n')
    except Exception as e:
        log(f"Failed to write to CSV log: {e}", RED, write_file=False)

class MLArenaMatchmaker:
    def __init__(self, slot_index=1):
        self.api_key = None
        self.student_id = None
        self.slot_id = None
        self.slot_index = slot_index
        self.slot_name = f"Slot {slot_index}"
        
        # Monitoring stats
        self.tracked_battles = {}
        self.session_wins = 0
        self.session_losses = 0
        self.session_draws = 0
        self.initial_elo = 1000.0
        self.current_elo = 1000.0
        self.initial_games = 0
        self.current_games = 0
        self.last_processed_battle_id = 0
        self.stamina_cooldown_until = 0.0
        
        self.load_credentials()

    def load_credentials(self):
        # Look for credentials file
        paths_to_try = [
            "homework_account.json",
            "../rl_starter_11/homework_account.json",
            "../rl_starter_12/homework_account.json"
        ]
        
        credentials_loaded = False
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.api_key = data.get("api_key")
                        self.student_id = data.get("account")
                        log(f"Loaded credentials from '{path}' (Account: {self.student_id})", GREEN)
                        credentials_loaded = True
                        break
                except Exception as e:
                    log(f"Error reading {path}: {e}", RED)
        
        if not credentials_loaded or not self.api_key:
            # Fallback to default user key
            self.api_key = "a738064d-5d7a-492d-86f6-d2dff6568e22"
            self.student_id = "41241213S"
            log(f"Using default fallback credentials (Account: {self.student_id})", YELLOW)

    def api_request(self, endpoint, method="GET", body=None):
        url = f"{API_BASE}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("X-API-Key", self.api_key)
        req.add_header("User-Agent", USER_AGENT)
        
        req_data = None
        if body is not None:
            req.add_header("Content-Type", "application/json")
            req_data = json.dumps(body).encode("utf-8")

        try:
            with urllib.request.urlopen(req, data=req_data, timeout=15) as response:
                content = response.read()
                if not content:
                    return {"success": True, "status": response.status}
                return json.loads(content.decode())
        except urllib.error.HTTPError as e:
            err_content = e.read().decode()
            log(f"HTTP Error {e.code} on {method} {endpoint}: {err_content}", RED)
            try:
                return json.loads(err_content)
            except:
                return {"error": err_content}
        except Exception as e:
            log(f"Network error on {method} {endpoint}: {e}", RED)
            return None

    def resolve_slot(self):
        log(f"Fetching slots for competition {COMPETITION_ID}...", CYAN)
        slots = self.api_request(f"/rl/competitions/{COMPETITION_ID}/slots")
        if not slots or not isinstance(slots, list):
            log("Failed to retrieve slots from API.", RED)
            sys.exit(1)

        # Print slots summary
        log("Available slots:", CYAN)
        for s in slots:
            log(f"  - Slot {s.get('slot_index')}: {s.get('name')} (ID: {s.get('id')}) | ELO: {s.get('elo_rating'):.1f} | Games: {s.get('elo_games_played')}")

        # Find target slot
        target = None
        for s in slots:
            if s.get("slot_index") == self.slot_index:
                target = s
                break
        
        if target:
            self.slot_id = target.get("id")
            self.slot_name = target.get("name")
            self.initial_elo = target.get("elo_rating", 1000.0)
            self.current_elo = self.initial_elo
            self.initial_games = target.get("elo_games_played", 0)
            self.current_games = self.initial_games
            log(f"Resolved target slot: {self.slot_name} (ID: {self.slot_id})", GREEN + BOLD)
            log(f"Initial Elo: {self.initial_elo:.2f} | Total Matches Played: {self.initial_games}", CYAN)
        else:
            log(f"Could not find slot with index {self.slot_index}.", RED)
            sys.exit(1)

    def resolve_slot_rating_only(self):
        slots = self.api_request(f"/rl/competitions/{COMPETITION_ID}/slots")
        if slots and isinstance(slots, list):
            for s in slots:
                if s.get("id") == self.slot_id:
                    self.current_elo = s.get("elo_rating", 1000.0)
                    self.current_games = s.get("elo_games_played", 0)
                    break

    def get_recent_battles(self):
        res = self.api_request(f"/rl/competitions/{COMPETITION_ID}/battles?page=1&limit=10")
        if isinstance(res, list):
            return res
        elif isinstance(res, dict) and "items" in res:
            return res["items"]
        return []

    def find_last_battle_id(self):
        battles = self.get_recent_battles()
        for b in battles:
            participants = b.get("participants", [])
            for p in participants:
                if p.get("rl_slot_id") == self.slot_id:
                    return b.get("id", 0)
        return 0

    def scan_for_new_battles(self):
        battles = self.get_recent_battles()
        new_battles = []
        for b in battles:
            bid = b.get("id", 0)
            if bid > self.last_processed_battle_id:
                participants = b.get("participants", [])
                is_me = False
                for p in participants:
                    if p.get("rl_slot_id") == self.slot_id:
                        is_me = True
                        break
                if is_me:
                    new_battles.append(b)
                    
        # Sort ascending by ID to process oldest first
        new_battles.sort(key=lambda x: x.get("id", 0))
        for b in new_battles:
            bid = b.get("id", 0)
            log(f"Match found! Session ID: {bid}", GREEN + BOLD)
            log(f"Battle URL: https://mlarena.spkuan.cc/rl/battles/{bid}", MAGENTA + BOLD)
            
            # Register in tracked battles
            self.tracked_battles[bid] = {"status": "running"}
            self.last_processed_battle_id = bid

    def check_queue_status(self):
        return self.api_request(f"/rl/competitions/{COMPETITION_ID}/queue/status")

    def join_queue(self):
        log(f"Joining matchmaking queue for slot {self.slot_name} (ID: {self.slot_id})...", YELLOW)
        res = self.api_request(f"/rl/competitions/{COMPETITION_ID}/queue", method="POST", body={"slot_id": self.slot_id})
        if res and res.get("in_queue"):
            log("Successfully joined queue!", GREEN)
            return True
        else:
            log(f"Failed to join queue. Response: {res}", RED)
            # 💡 新增：如果伺服器回傳 detail 包含體力不足，立刻啟動 120 秒智慧冷卻時間戳
            if res and isinstance(res, dict) and "Not enough stamina" in str(res.get("detail", "")):
                log("[Stamina Depleted] Activating 120-second smart cooldown.", RED + BOLD)
                self.stamina_cooldown_until = time.time() + 120
            return False

    def leave_queue(self):
        log("Leaving matchmaking queue...", YELLOW)
        res = self.api_request(f"/rl/competitions/{COMPETITION_ID}/queue", method="DELETE")
        if res and (res.get("success") or res.get("status") == 204):
            log("Successfully left queue.", GREEN)
            return True
        else:
            log(f"Failed to leave queue. Response: {res}", RED)
            return False

    def start(self):
        self.resolve_slot()
        
        # Initialize last processed battle ID from history
        self.last_processed_battle_id = self.find_last_battle_id()
        log(f"Initialized last processed battle ID: {self.last_processed_battle_id}", CYAN)
        
        # Check initial status
        status = self.check_queue_status()
        if not status:
            log("Unable to get queue status. Exiting.", RED)
            sys.exit(1)
            
        in_queue = status.get("in_queue", False)
        current_slot_id = status.get("slot_id")
        
        if in_queue:
            if current_slot_id == self.slot_id:
                log(f"Already in queue with target slot {self.slot_name}.", GREEN)
            else:
                log(f"Currently in queue with a different slot (ID: {current_slot_id}). Switching to {self.slot_name}...", YELLOW)
                self.leave_queue()
                time.sleep(1)
                self.join_queue()
        else:
            self.join_queue()

        log("Matchmaker loop started. Press Ctrl+C to cancel and leave queue.", CYAN + BOLD)
        consecutive_errors = 0
        
        while True:
            try:
                # 0. Scan for any new matches (fixes race condition where match starts before queue status polls)
                self.scan_for_new_battles()

                # 1. Process tracked battles that are still running
                for bid in list(self.tracked_battles.keys()):
                    bdata = self.tracked_battles[bid]
                    if bdata["status"] == "running":
                        bdetail = self.api_request(f"/rl/battles/{bid}")
                        if bdetail and bdetail.get("status") == "completed":
                            participants = bdetail.get("participants", [])
                            me = None
                            opponent = None
                            for p in participants:
                                if p.get("rl_slot_id") == self.slot_id:
                                    me = p
                                else:
                                    opponent = p
                                    
                            if me:
                                rank = me.get("final_rank")
                                elo_delta = me.get("elo_delta")
                                if elo_delta is None:
                                    elo_delta = 0.0
                                    
                                # Wait a brief moment and fetch refreshed slot info
                                time.sleep(1.5)
                                self.resolve_slot_rating_only()
                                
                                elo_change = elo_delta
                                elo_after = self.current_elo
                                elo_before = elo_after - elo_change
                                
                                opp_name = opponent.get("username") if opponent else "Unknown"
                                opp_elo = opponent.get("elo_before", 0) if opponent else 0
                                if opp_name is None:
                                    opp_name = f"Guest (Slot ID {opponent.get('rl_slot_id')})" if opponent else "Unknown"
                                
                                if rank == 1 or str(rank) == "1":
                                    self.session_wins += 1
                                    result_str = f"{GREEN}WIN 🏆{RESET}"
                                    csv_result = "WIN"
                                elif rank == 2 or str(rank) == "2" or (elo_change is not None and elo_change < 0):
                                    self.session_losses += 1
                                    result_str = f"{RED}LOSS ❌{RESET}"
                                    csv_result = "LOSS"
                                else:
                                    self.session_draws += 1
                                    result_str = f"{YELLOW}DRAW 🤝{RESET}"
                                    csv_result = "DRAW"
                                    
                                log(f"Battle #{bid} Completed! Result: {result_str} vs {opp_name} (Elo: {opp_elo:.1f})", GREEN + BOLD)
                                if elo_before and elo_after:
                                    log(f"  Elo Change: {elo_before:.1f} -> {elo_after:.1f} ({elo_change:+.2f})", CYAN)
                                elif elo_change:
                                    log(f"  Elo Change: {elo_change:+.2f}", CYAN)
                                    
                                # Write structured match entry to CSV
                                log_match_csv(bid, opp_name, opp_elo, csv_result, elo_before, elo_after, elo_change)
                                    
                                total_games = self.session_wins + self.session_losses + self.session_draws
                                win_rate = (self.session_wins / total_games * 100) if total_games > 0 else 0
                                log(f"Session Stats: {self.session_wins}W - {self.session_losses}L - {self.session_draws}D (Win Rate: {win_rate:.1f}%) | Total Elo Delta: {self.current_elo - self.initial_elo:+.2f}", MAGENTA + BOLD)
                                log(f"Leaderboard: Current Elo: {self.current_elo:.1f} | Total Games: {self.current_games}", CYAN)
                                
                                if csv_result == "LOSS":
                                    log(f"{self.slot_name} has lost a single match! Leaving queue and stopping matchmaker immediately.", RED + BOLD)
                                    self.leave_queue()
                                    sys.exit(0)
                                
                            bdata["status"] = "completed"

                # 2. Poll current queue status
                time.sleep(5)
                status = self.check_queue_status()
                
                if status is None:
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        log("Too many connection errors. Exiting loop.", RED)
                        break
                    continue
                
                consecutive_errors = 0
                in_queue = status.get("in_queue", False)
                wait_seconds = status.get("wait_seconds", 0)
                queue_state = status.get("status")

                if in_queue:
                    log(f"In queue... Status: {queue_state} | Elapsed: {wait_seconds}s", CYAN)
                else:
                    # 💡 1. 優先檢查是否處於體力冷卻期
                    current_time = time.time()
                    if current_time < self.stamina_cooldown_until:
                        remaining = int(self.stamina_cooldown_until - current_time)
                        log(f"Out of stamina. Waiting for regeneration... ({remaining}s remaining)", YELLOW)
                        time.sleep(10)  # 冷卻期內每 10 秒提示一次即可，不戳 API
                        continue

                    # 💡 2. 雙重防禦：檢查當前是否有正在進行的對局，避免比賽中誤戳排隊
                    has_running_battle = any(bdata["status"] == "running" for bdata in self.tracked_battles.values())
                    if has_running_battle:
                        log("Battle is currently in progress. Waiting for result...", MAGENTA)
                    else:
                        # 💡 3. 既沒排隊也沒在比賽，且冷卻已過，這時才安全發起排隊
                        log("Not in queue. Re-queueing...", YELLOW)
                        self.join_queue()   
                             
            except KeyboardInterrupt:
                print("\n")
                log("KeyboardInterrupt detected. Cleaning up...", YELLOW)
                self.leave_queue()
                log("Exited gracefully.", GREEN)
                break
            except Exception as e:
                log(f"Error in matchmaker loop: {e}", RED)
                time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ML Arena Chess Matchmaker")
    parser.add_argument("--slot", type=int, default=1, choices=[0, 1, 2], help="Slot index (default: 1)")
    args = parser.parse_args()

    matchmaker = MLArenaMatchmaker(slot_index=args.slot)
    matchmaker.start()
