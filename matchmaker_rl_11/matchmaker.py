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
        
        # Add new state variables
        self.mode = "queue"
        self.lost_opponents = set()
        self.loss_count = 0
        self.failed_challenges = {}
        self.state_file = "matchmaker_state.json"
        self.exit_requested = False
        
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

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.loss_count = data.get("loss_count", 0)
                    self.lost_opponents = set(data.get("lost_opponents", []))
                    self.mode = data.get("mode", "queue")
                    log(f"Loaded persistent state from {self.state_file}: loss_count={self.loss_count}, lost_opponents={self.lost_opponents}, mode={self.mode}", GREEN)
            except Exception as e:
                log(f"Error loading state from {self.state_file}: {e}", RED)

    def save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "loss_count": self.loss_count,
                    "lost_opponents": list(self.lost_opponents),
                    "mode": self.mode
                }, f, indent=2, ensure_ascii=False)
            log(f"Saved persistent state to {self.state_file}", GREEN)
        except Exception as e:
            log(f"Error saving state to {self.state_file}: {e}", RED)

    def is_after_june_8(self, created_at_str):
        if not created_at_str:
            return False
        # UTC threshold for 2026-06-08 00:00:00+08:00 is 2026-06-07T16:00:00Z.
        ts = created_at_str.replace("Z", "")
        if "." in ts:
            ts = ts.split(".")[0]
        return ts >= "2026-06-07T16:00:00"

    def initialize_history(self):
        log("Initializing history and tracking lost opponents since June 8...", CYAN)
        self.load_state()
        
        # Scan history from API if we do not have a state file
        if not os.path.exists(self.state_file):
            log("No state file found. Scanning API history...", CYAN)
            url = f"/rl/competitions/{COMPETITION_ID}/battles?page=1&limit=50"
            battles = self.api_request(url)
            if not isinstance(battles, list):
                if isinstance(battles, dict) and "items" in battles:
                    battles = battles["items"]
                else:
                    battles = []
            
            # Sort ascending so we process oldest first
            battles.sort(key=lambda x: x.get("id", 0))
            
            for b in battles:
                if b.get("status") != "completed":
                    continue
                created_at = b.get("created_at")
                if not self.is_after_june_8(created_at):
                    continue
                    
                participants = b.get("participants", [])
                me = None
                opponent = None
                for p in participants:
                    if p.get("rl_slot_id") == self.slot_id:
                        me = p
                    else:
                        opponent = p
                        
                if me and opponent:
                    elo_delta = me.get("elo_delta")
                    rank = me.get("final_rank")
                    opp_username = opponent.get("username")
                    opp_user_id = opponent.get("user_id")
                    
                    is_loss = False
                    if elo_delta is not None and elo_delta < 0:
                        is_loss = True
                    elif rank == 2 or str(rank) == "2":
                        is_loss = True
                    elif rank is not None and opponent.get("final_rank") is not None and rank > opponent.get("final_rank"):
                        is_loss = True
                        
                    if is_loss:
                        if opp_username:
                            self.lost_opponents.add(opp_username)
                        if opp_user_id:
                            self.lost_opponents.add(opp_user_id)
                        self.loss_count += 1
            
            self.save_state()
        else:
            log(f"Using loaded state. Loss count: {self.loss_count}/2", GREEN)

    def determine_initial_mode(self):
        log("Determining initial mode from latest battle since June 8...", CYAN)
        if os.path.exists(self.state_file):
            log(f"Mode loaded from state file: {self.mode}", GREEN)
            return

        battles = self.get_recent_battles()
        my_battles = []
        for b in battles:
            if b.get("status") != "completed":
                continue
            created_at = b.get("created_at")
            if not self.is_after_june_8(created_at):
                continue
            participants = b.get("participants", [])
            for p in participants:
                if p.get("rl_slot_id") == self.slot_id:
                    my_battles.append(b)
                    break
        if not my_battles:
            log("No previous completed battles found since June 8. Defaulting to 'queue' mode.", GREEN)
            self.mode = "queue"
            return
            
        my_battles.sort(key=lambda x: x.get("id", 0), reverse=True)
        latest = my_battles[0]
        
        me = None
        for p in latest.get("participants", []):
            if p.get("rl_slot_id") == self.slot_id:
                me = p
                break
        if me:
            elo_delta = me.get("elo_delta")
            if elo_delta is not None and elo_delta > 0:
                log(f"Latest battle #{latest.get('id')} was a WIN. Setting initial mode to 'queue'.", GREEN)
                self.mode = "queue"
            else:
                log(f"Latest battle #{latest.get('id')} was a DRAW/LOSS. Setting initial mode to 'challenge'.", YELLOW)
                self.mode = "challenge"
        else:
            self.mode = "queue"
        self.save_state()

    def get_my_latest_battle(self):
        battles = self.get_recent_battles()
        for b in battles:
            participants = b.get("participants", [])
            for p in participants:
                if p.get("rl_slot_id") == self.slot_id:
                    return b
        return None

    def find_best_opponent(self):
        log("Fetching leaderboard to find the best opponent...", CYAN)
        leaderboard = self.api_request(f"/rl/competitions/{COMPETITION_ID}/leaderboard")
        if not isinstance(leaderboard, list):
            log("Failed to retrieve leaderboard.", RED)
            return None
            
        valid_opponents = []
        for item in leaderboard:
            user_id = item.get("user_id")
            username = item.get("username")
            slot_id = item.get("slot_id")
            slot_name = item.get("slot_name")
            elo = item.get("elo_rating", 1000.0)
            
            if slot_id == self.slot_id or user_id == self.student_id or username == self.student_id:
                continue
                
            if not slot_id or slot_id == 0 or slot_name == "—" or not slot_name:
                continue
                
            if username in self.lost_opponents or user_id in self.lost_opponents:
                continue
                
            if self.failed_challenges.get(user_id, 0) >= 3:
                continue
                
            valid_opponents.append({
                "user_id": user_id,
                "username": username,
                "elo": elo,
                "slot_name": slot_name
            })
            
        if not valid_opponents:
            log("No valid opponents found to challenge!", RED)
            return None
            
        valid_opponents.sort(key=lambda x: x["elo"], reverse=True)
        best = valid_opponents[0]
        log(f"Best opponent found: {best['username']} (Elo: {best['elo']:.1f}, Slot: {best['slot_name']})", GREEN)
        return best

    def challenge_player(self, opponent_user_id):
        log(f"Challenging player (User ID: {opponent_user_id})...", YELLOW)
        body = {
            "competition_id": COMPETITION_ID,
            "attacker_slot_id": self.slot_id,
            "target_user_ids": [opponent_user_id]
        }
        res = self.api_request("/rl/battles/challenge", method="POST", body=body)
        if res and isinstance(res, dict) and "id" in res:
            log(f"Successfully initiated challenge! Battle ID: {res['id']}", GREEN)
            self.failed_challenges[opponent_user_id] = 0
            # Track it
            self.tracked_battles[res["id"]] = {"status": "running"}
            return res
        else:
            log(f"Failed to initiate challenge. Response: {res}", RED)
            if res and isinstance(res, dict) and "Not enough stamina" in str(res.get("detail", "")):
                log("[Stamina Depleted] Activating 120-second smart cooldown.", RED + BOLD)
                self.stamina_cooldown_until = time.time() + 120
            else:
                self.failed_challenges[opponent_user_id] = self.failed_challenges.get(opponent_user_id, 0) + 1
            return None

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

    def process_battle_result(self, battle):
        bid = battle.get("id")
        status = battle.get("status")
        log(f"Processing result for Battle #{bid} (Status: {status})", GREEN + BOLD)
        
        if status == "failed":
            log(f"Battle #{bid} failed. Error message: {battle.get('error_message')}", RED)
            self.mode = "queue"
            self.save_state()
            return
            
        participants = battle.get("participants", [])
        me = None
        opponent = None
        for p in participants:
            if p.get("rl_slot_id") == self.slot_id:
                me = p
            else:
                opponent = p
                
        if not me:
            log(f"Warning: Could not find our slot ID {self.slot_id} in battle #{bid}.", YELLOW)
            return

        rank = me.get("final_rank")
        elo_delta = me.get("elo_delta")
        if elo_delta is None:
            elo_delta = 0.0
            
        # Refresh rating
        time.sleep(1.5)
        self.resolve_slot_rating_only()
        
        elo_change = elo_delta
        elo_after = self.current_elo
        elo_before = elo_after - elo_change
        
        opp_name = opponent.get("username") if opponent else "Unknown"
        opp_user_id = opponent.get("user_id") if opponent else None
        opp_elo = opponent.get("elo_before", 0) if opponent else 0
        if opp_name is None:
            opp_name = f"Guest (Slot ID {opponent.get('rl_slot_id')})" if opponent else "Unknown"
            
        won = elo_delta > 0
        is_loss = False
        if elo_delta < 0:
            is_loss = True
        elif rank == 2 or str(rank) == "2":
            is_loss = True
        elif rank is not None and opponent and opponent.get("final_rank") is not None and rank > opponent.get("final_rank"):
            is_loss = True

        if won:
            self.session_wins += 1
            result_str = f"{GREEN}WIN 🏆{RESET}"
            csv_result = "WIN"
            self.mode = "queue"
        elif is_loss:
            self.session_losses += 1
            self.loss_count += 1
            result_str = f"{RED}LOSS ❌{RESET}"
            csv_result = "LOSS"
            self.mode = "challenge"
            if opponent and opponent.get("username"):
                self.lost_opponents.add(opponent.get("username"))
            if opp_user_id:
                self.lost_opponents.add(opp_user_id)
        else:
            self.session_draws += 1
            result_str = f"{YELLOW}DRAW 🤝{RESET}"
            csv_result = "DRAW"
            self.mode = "challenge"
            
        log(f"Battle #{bid} Completed! Result: {result_str} vs {opp_name} (Elo: {opp_elo:.1f})", GREEN + BOLD)
        log(f"  Elo Change: {elo_before:.1f} -> {elo_after:.1f} ({elo_change:+.2f})", CYAN)
        
        # Write to CSV log
        log_match_csv(bid, opp_name, opp_elo, csv_result, elo_before, elo_after, elo_change)
        
        # Save updated state
        self.save_state()
        
        total_games = self.session_wins + self.session_losses + self.session_draws
        win_rate = (self.session_wins / total_games * 100) if total_games > 0 else 0
        log(f"Session Stats: {self.session_wins}W - {self.session_losses}L - {self.session_draws}D (Win Rate: {win_rate:.1f}%) | Total Elo Delta: {self.current_elo - self.initial_elo:+.2f}", MAGENTA + BOLD)
        log(f"Leaderboard: Current Elo: {self.current_elo:.1f} | Total Games: {self.current_games}", CYAN)
        log(f"Session Loss Count: {self.loss_count}/2 | Lost Opponents: {self.lost_opponents}", CYAN)
        
        if self.loss_count >= 2:
            log(f"{self.slot_name} has accumulated {self.loss_count} losses! Leaving queue and stopping matchmaker immediately.", RED + BOLD)
            self.leave_queue()
            sys.exit(0)

    def start(self):
        self.resolve_slot()
        
        # Load state and initialize history from June 8 onwards
        self.initialize_history()
        
        # Check initial battle status to set last_processed_battle_id
        latest_battle = self.get_my_latest_battle()
        if latest_battle:
            bid = latest_battle.get("id")
            status = latest_battle.get("status")
            if status in ["pending", "running"]:
                # If active, we want to process it when it completes
                self.last_processed_battle_id = bid - 1
                log(f"Latest battle #{bid} is currently {status}. Will process when finished.", CYAN)
            else:
                self.last_processed_battle_id = bid
                log(f"Latest battle #{bid} is already completed/failed. Last processed ID: {self.last_processed_battle_id}", CYAN)
                self.determine_initial_mode()
        else:
            self.last_processed_battle_id = 0
            self.determine_initial_mode()
            
        log("Matchmaker loop started. Press Ctrl+C to cancel and leave queue.", CYAN + BOLD)
        consecutive_errors = 0
        
        while True:
            try:
                # If the user requested to exit, check if we can stop
                if self.exit_requested:
                    # Check if there is an active battle
                    latest_battle = self.get_my_latest_battle()
                    battle_active = latest_battle is not None and latest_battle.get("status") in ["pending", "running"]
                    if battle_active:
                        log(f"Graceful shutdown requested. Waiting for active Battle #{latest_battle.get('id')} to finish...", MAGENTA)
                    else:
                        log("No active battles. Leaving queue and exiting gracefully.", GREEN)
                        self.leave_queue()
                        sys.exit(0)

                # 0. Check stamina cooldown
                current_time = time.time()
                if current_time < self.stamina_cooldown_until:
                    remaining = int(self.stamina_cooldown_until - current_time)
                    log(f"Out of stamina. Waiting for regeneration... ({remaining}s remaining)", YELLOW)
                    time.sleep(10)
                    continue

                # 1. Fetch current status
                status = self.check_queue_status()
                if status is None:
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        log("Too many connection errors. Exiting loop.", RED)
                        break
                    time.sleep(5)
                    continue
                consecutive_errors = 0
                
                in_queue = status.get("in_queue", False)
                wait_seconds = status.get("wait_seconds", 0)
                queue_state = status.get("status")
                
                # Check for active battles
                latest_battle = self.get_my_latest_battle()
                battle_active = latest_battle is not None and latest_battle.get("status") in ["pending", "running"]
                
                # 2. Process finished battles
                if latest_battle:
                    bid = latest_battle.get("id")
                    if bid > self.last_processed_battle_id and latest_battle.get("status") not in ["pending", "running"]:
                        self.process_battle_result(latest_battle)
                        self.last_processed_battle_id = bid
                        time.sleep(2)
                        continue

                # 3. Handle active/waiting state
                if battle_active:
                    log(f"Battle #{latest_battle.get('id')} is currently in progress. Status: {latest_battle.get('status')}. Waiting...", MAGENTA)
                    time.sleep(5)
                    continue
                    
                if in_queue:
                    log(f"In queue... Status: {queue_state} | Elapsed: {wait_seconds}s", CYAN)
                    time.sleep(5)
                    continue
                    
                # 4. Action state (not in queue, no battle active)
                if self.mode == "queue":
                    log("Not in queue. Re-queueing...", YELLOW)
                    self.join_queue()
                elif self.mode == "challenge":
                    opp = self.find_best_opponent()
                    if opp:
                        self.challenge_player(opp["user_id"])
                    else:
                        log("No valid opponents to challenge. Falling back to queueing.", YELLOW)
                        self.join_queue()
                        
                time.sleep(5)

            except KeyboardInterrupt:
                print("\n")
                if self.exit_requested:
                    log("Force exit requested. Exiting immediately.", RED)
                    self.leave_queue()
                    sys.exit(1)
                
                # Set exit requested flag
                self.exit_requested = True
                log("KeyboardInterrupt detected. Graceful shutdown initiated.", YELLOW)
                
                # Check if there is an active battle right now
                latest_battle = self.get_my_latest_battle()
                battle_active = latest_battle is not None and latest_battle.get("status") in ["pending", "running"]
                
                if battle_active:
                    log(f"Waiting for current Battle #{latest_battle.get('id')} to finish before stopping. Press Ctrl+C again to force quit.", YELLOW + BOLD)
                else:
                    log("No active battles. Leaving queue and exiting gracefully.", GREEN)
                    self.leave_queue()
                    sys.exit(0)
                    
            except Exception as e:
                log(f"Error in matchmaker loop: {e}", RED)
                import traceback
                traceback.print_exc()
                time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ML Arena Chess Matchmaker")
    parser.add_argument("--slot", type=int, default=1, choices=[0, 1, 2], help="Slot index (default: 1)")
    args = parser.parse_args()

    matchmaker = MLArenaMatchmaker(slot_index=args.slot)
    matchmaker.start()
