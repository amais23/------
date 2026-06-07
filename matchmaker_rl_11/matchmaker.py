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
import random
import math
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
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(script_dir, "matchmaker.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(clean_msg + "\n")
        except Exception:
            pass

def log_match_csv(battle_id, opponent, opponent_elo, result, elo_before, elo_after, elo_change):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "match_history.csv")
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
    def __init__(self, slot_index=2):
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
        self.mode = "challenge"
        self.avoid_opponents = set()
        self.processed_battle_ids = set()
        self.loss_count = 0
        self.failed_challenges = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_file = os.path.join(script_dir, "matchmaker_state.json")
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
                    
                    # Migrate old state
                    lost_opps = data.get("lost_opponents", [])
                    avoid_opps = data.get("avoid_opponents", [])
                    self.avoid_opponents = set(avoid_opps) | set(lost_opps)
                    
                    self.processed_battle_ids = set(data.get("processed_battle_ids", []))
                    self.mode = data.get("mode", "challenge")
                    log(f"Loaded persistent state from {self.state_file}: loss_count={self.loss_count}, avoid_opponents={self.avoid_opponents}, processed_battle_ids={len(self.processed_battle_ids)} ids, mode={self.mode}", GREEN)
            except Exception as e:
                log(f"Error loading state from {self.state_file}: {e}", RED)

    def save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "loss_count": self.loss_count,
                    "avoid_opponents": list(self.avoid_opponents),
                    "processed_battle_ids": list(self.processed_battle_ids),
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
        log("Initializing history and tracking avoided opponents since June 8...", CYAN)
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
                status = b.get("status")
                created_at = b.get("created_at")
                if not self.is_after_june_8(created_at):
                    continue
                    
                bid = b.get("id")
                if bid:
                    self.processed_battle_ids.add(bid)
                    
                participants = b.get("participants", [])
                me = None
                opponent = None
                for p in participants:
                    if p.get("rl_slot_id") == self.slot_id:
                        me = p
                    else:
                        opponent = p
                        
                if opponent:
                    opp_username = str(opponent.get("username")) if opponent.get("username") is not None else None
                    opp_user_id = str(opponent.get("user_id")) if opponent.get("user_id") is not None else None
                    
                    if status == "failed":
                        # Failed battles are usually due to server timeout, not the opponent.
                        # We no longer penalize opponents for failed battles.
                        pass
                    elif status == "completed" and me:
                        elo_delta = me.get("elo_delta")
                        rank = me.get("final_rank")
                        opp_rank = opponent.get("final_rank")
                        
                        is_loss_or_elo_dropping_draw = False
                        if elo_delta is not None and elo_delta < 0:
                            is_loss_or_elo_dropping_draw = True
                        elif rank == 2 or str(rank) == "2":
                            is_loss_or_elo_dropping_draw = True
                        elif rank is not None and opp_rank is not None and rank > opp_rank:
                            is_loss_or_elo_dropping_draw = True
                            
                        if is_loss_or_elo_dropping_draw:
                            if opp_username:
                                self.avoid_opponents.add(opp_username)
                            if opp_user_id:
                                self.avoid_opponents.add(opp_user_id)
                            self.loss_count += 1
            
            self.save_state()
        else:
            log(f"Using loaded state. Avoided opponents: {len(self.avoid_opponents)}", GREEN)

    def determine_initial_mode(self):
        log("Forcing initial mode to 'challenge' as requested.", GREEN)
        self.mode = "challenge"
        self.save_state()

    def process_finished_battles(self):
        recent_battles = self.get_recent_battles()
        if not isinstance(recent_battles, list):
            return
            
        recent_battles.sort(key=lambda x: x.get("id", 0))
        
        for b in recent_battles:
            bid = b.get("id")
            if not bid:
                continue
                
            if bid in self.processed_battle_ids:
                continue
                
            participants = b.get("participants", [])
            is_me_participant = False
            for p in participants:
                if p.get("rl_slot_id") == self.slot_id:
                    is_me_participant = True
                    break
                    
            if not is_me_participant:
                continue
                
            status = b.get("status")
            if status in ["pending", "running"]:
                continue
                
            self.process_battle_result(b)
            self.processed_battle_ids.add(bid)
            
        if len(self.processed_battle_ids) > 1000:
            sorted_ids = sorted(list(self.processed_battle_ids))
            self.processed_battle_ids = set(sorted_ids[-500:])
            
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
        log("Fetching leaderboard to find a weighted random opponent...", CYAN)
        leaderboard = self.api_request(f"/rl/competitions/{COMPETITION_ID}/leaderboard")
        if not isinstance(leaderboard, list):
            log("Failed to retrieve leaderboard.", RED)
            return None
            
        valid_opponents = []
        for item in leaderboard:
            user_id = str(item.get("user_id")) if item.get("user_id") is not None else None
            username = str(item.get("username")) if item.get("username") is not None else None
            slot_id = item.get("slot_id")
            slot_name = item.get("slot_name")
            elo = item.get("elo_rating", 1000.0)
            
            # Exclude self
            if slot_id == self.slot_id or user_id == str(self.student_id) or username == str(self.student_id):
                continue
                
            # Filter only those who have agents
            if not slot_id or slot_id == 0 or slot_name == "—" or not slot_name:
                continue
                
            # Exclude avoided opponents
            if username in self.avoid_opponents or user_id in self.avoid_opponents:
                continue
                
            # Exclude temporarily failed challenge API targets
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
            
        # Select randomly based on ELO weighting: w = 10^(E/400)
        weights = [10 ** (opp["elo"] / 400.0) for opp in valid_opponents]
        chosen = random.choices(valid_opponents, weights=weights, k=1)[0]
        log(f"Selected opponent: {chosen['username']} (Elo: {chosen['elo']:.1f}, Slot: {chosen['slot_name']}) out of {len(valid_opponents)} candidates.", GREEN)
        return chosen

    def challenge_player(self, opponent):
        opponent_user_id = opponent["user_id"]
        log(f"Challenging player {opponent.get('username')} (User ID: {opponent_user_id})...", YELLOW)
        body = {
            "competition_id": COMPETITION_ID,
            "attacker_slot_id": self.slot_id,
            "target_user_ids": [opponent_user_id]
        }
        
        # Save current challenged opponent info for failed battle fallback
        self.current_challenged_opponent = opponent
        
        res = self.api_request("/rl/battles/challenge", method="POST", body=body)
        if res and isinstance(res, dict) and "id" in res:
            log(f"Successfully initiated challenge! Battle ID: {res['id']}", GREEN)
            self.failed_challenges[opponent_user_id] = 0
            self.tracked_battles[res["id"]] = {"status": "running", "opponent": opponent}
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
        res = self.api_request(f"/rl/competitions/{COMPETITION_ID}/battles?page=1&limit=100")
        if isinstance(res, list):
            return res
        elif isinstance(res, dict) and "items" in res:
            return res["items"]
        return []

    def fetch_battle_replay(self, battle_id):
        """
        Fetch the full game transcript (replay) for a given battle via the API.
        Returns a dict with keys:
          - 'games'  (int): total number of episodes played
          - 'wins'   (list[int]): win counts per player index
          - 'draws'  (int): number of drawn episodes
          - 'steps'  (list[dict]): each step has 'game', 'step', 'player', 'action'
        Returns None on failure.
        """
        log(f"Fetching replay for battle #{battle_id}...", CYAN)
        res = self.api_request(f"/rl/battles/{battle_id}/replay")
        if res and isinstance(res, dict) and "steps" in res:
            log(f"Replay fetched: {res.get('games')} games, "
                f"wins={res.get('wins')}, draws={res.get('draws')}, "
                f"total steps={len(res.get('steps', []))}", GREEN)
            return res
        else:
            log(f"Failed to fetch replay for battle #{battle_id}. Response: {res}", RED)
            return None

    def log_battle_replay(self, battle_id):
        """
        Fetch and print a human-readable summary of each episode in a battle.
        Useful for debugging server draw bugs (see server_drow_bug.md).
        """
        replay = self.fetch_battle_replay(battle_id)
        if not replay:
            return
        steps = replay.get("steps", [])
        games = replay.get("games", 0)
        wins = replay.get("wins", [])
        draws = replay.get("draws", 0)
        log(f"=== Replay Summary for Battle #{battle_id} ===", CYAN + BOLD)
        log(f"  Episodes: {games} | Wins by player: {wins} | Draws: {draws}", CYAN)
        # Group steps by game
        from collections import defaultdict
        by_game = defaultdict(list)
        for s in steps:
            by_game[s["game"]].append(s)
        for g in sorted(by_game.keys()):
            ep_steps = by_game[g]
            log(f"  Episode {g}: {len(ep_steps)} steps", CYAN)
        log(f"=== End of Replay Summary ===", CYAN + BOLD)

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
        
        # Add to processed set
        self.processed_battle_ids.add(bid)
        
        if status == "failed":
            log(f"Battle #{bid} failed (likely server timeout). Error message: {battle.get('error_message')}", RED)
            # Failed battles are usually due to server timeout—both sides push compute to the limit.
            # We do NOT penalize the opponent for a server-side failure.
            
            # Find opponent name and user ID (for CSV logging only)
            opp_name = "Unknown"
            opp_user_id = None
            opp_elo = 0.0
            
            participants = battle.get("participants", [])
            opp_part = None
            for p in participants:
                if p.get("rl_slot_id") != self.slot_id:
                    opp_part = p
                    break
            
            if opp_part:
                opp_name = opp_part.get("username") or f"Guest (Slot ID {opp_part.get('rl_slot_id')})"
                opp_user_id = opp_part.get("user_id")
                opp_elo = opp_part.get("elo_before") or 0.0
            elif hasattr(self, 'current_challenged_opponent') and self.current_challenged_opponent:
                opp_name = self.current_challenged_opponent.get("username", "Unknown")
                opp_user_id = self.current_challenged_opponent.get("user_id")
                opp_elo = self.current_challenged_opponent.get("elo", 0.0)
                
            opp_name_str = str(opp_name) if opp_name is not None else "Unknown"
                    
            log_match_csv(bid, opp_name_str, float(opp_elo), "FAIL", float(self.current_elo), float(self.current_elo), 0.0)
            self.mode = "challenge"
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
            
        opp_name_str = str(opp_name) if opp_name is not None else "Unknown"
        opp_user_id_str = str(opp_user_id) if opp_user_id is not None else None
            
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
            self.mode = "challenge"
        elif is_loss:
            self.session_losses += 1
            self.loss_count += 1
            result_str = f"{RED}LOSS ❌{RESET}"
            csv_result = "LOSS"
            self.mode = "challenge"
        else:
            self.session_draws += 1
            result_str = f"{YELLOW}DRAW 🤝{RESET}"
            csv_result = "DRAW"
            self.mode = "challenge"

        # ELO decrease or loss avoidance rule:
        should_avoid = False
        if is_loss:
            should_avoid = True
        elif elo_delta is not None and elo_delta < 0:
            should_avoid = True

        if should_avoid:
            if opp_name_str and opp_name_str != "Unknown":
                self.avoid_opponents.add(opp_name_str)
            if opp_user_id_str:
                self.avoid_opponents.add(opp_user_id_str)
            log(f"Added opponent {opp_name_str} ({opp_user_id_str}) to avoid list (due to loss or ELO-reducing draw).", YELLOW)
            
        log(f"Battle #{bid} Completed! Result: {result_str} vs {opp_name_str} (Elo: {opp_elo:.1f})", GREEN + BOLD)
        log(f"  Elo Change: {elo_before:.1f} -> {elo_after:.1f} ({elo_change:+.2f})", CYAN)
        
        # Write to CSV log
        log_match_csv(bid, opp_name_str, opp_elo, csv_result, elo_before, elo_after, elo_change)
        
        # Save updated state
        self.save_state()
        
        total_games = self.session_wins + self.session_losses + self.session_draws
        win_rate = (self.session_wins / total_games * 100) if total_games > 0 else 0
        log(f"Session Stats: {self.session_wins}W - {self.session_losses}L - {self.session_draws}D (Win Rate: {win_rate:.1f}%) | Total Elo Delta: {self.current_elo - self.initial_elo:+.2f}", MAGENTA + BOLD)
        log(f"Leaderboard: Current Elo: {self.current_elo:.1f} | Total Games: {self.current_games}", CYAN)
        log(f"Session Loss Count: {self.loss_count} | Avoided Opponents Count: {len(self.avoid_opponents)}", CYAN)

    def start(self):
        self.resolve_slot()
        
        # Ensure we are not in the queue
        self.leave_queue()
        
        # Load state and initialize history from June 8 onwards
        self.initialize_history()
        
        # Check initial battle status to set last_processed_battle_id and populate processed_battle_ids
        latest_battle = self.get_my_latest_battle()
        if latest_battle:
            bid = latest_battle.get("id")
            status = latest_battle.get("status")
            if status in ["pending", "running"]:
                self.last_processed_battle_id = bid - 1
                log(f"Latest battle #{bid} is currently {status}. Will process when finished.", CYAN)
            else:
                self.last_processed_battle_id = bid
                log(f"Latest battle #{bid} is already completed/failed. Last processed ID: {self.last_processed_battle_id}", CYAN)
                self.determine_initial_mode()
        else:
            self.last_processed_battle_id = 0
            self.determine_initial_mode()
            
        log("Matchmaker loop started. Press Ctrl+C to cancel.", CYAN + BOLD)
        
        while True:
            try:
                # If the user requested to exit, check if we can stop
                if self.exit_requested:
                    recent_battles = self.get_recent_battles()
                    any_active = False
                    if isinstance(recent_battles, list):
                        for b in recent_battles:
                            bid = b.get("id")
                            if bid not in self.processed_battle_ids:
                                participants = b.get("participants", [])
                                for p in participants:
                                    if p.get("rl_slot_id") == self.slot_id:
                                        if b.get("status") in ["pending", "running"]:
                                            any_active = True
                                            break
                                            
                    if any_active:
                        log("Graceful shutdown requested. Waiting for active battles to finish...", MAGENTA)
                        self.process_finished_battles()
                        time.sleep(10)
                        continue
                    else:
                        self.process_finished_battles()
                        log("No active battles. Exiting gracefully.", GREEN)
                        sys.exit(0)

                # 0. Check stamina cooldown
                current_time = time.time()
                if current_time < self.stamina_cooldown_until:
                    remaining = int(self.stamina_cooldown_until - current_time)
                    log(f"Out of stamina. Waiting for regeneration... ({remaining}s remaining)", YELLOW)
                    self.process_finished_battles()
                    time.sleep(10)
                    continue

                # 1. Process finished battles
                self.process_finished_battles()

                # 2. Challenge state (non-blocking)
                opp = self.find_best_opponent()
                if opp:
                    self.challenge_player(opp)
                    # Sleep a tiny bit to avoid hammering the API
                    time.sleep(2)
                else:
                    log("No valid opponents to challenge (all avoided or none match). Waiting 30 seconds...", YELLOW)
                    time.sleep(30)
                        
                time.sleep(5)

            except KeyboardInterrupt:
                print("\n")
                if self.exit_requested:
                    log("Force exit requested. Exiting immediately.", RED)
                    sys.exit(1)
                
                self.exit_requested = True
                log("KeyboardInterrupt detected. Graceful shutdown initiated.", YELLOW)
                
            except Exception as e:
                log(f"Error in matchmaker loop: {e}", RED)
                import traceback
                traceback.print_exc()
                time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ML Arena Chess Matchmaker")
    parser.add_argument("--slot", type=int, default=2, choices=[0, 1, 2], help="Slot index (default: 2)")
    args = parser.parse_args()

    matchmaker = MLArenaMatchmaker(slot_index=args.slot)
    matchmaker.start()
