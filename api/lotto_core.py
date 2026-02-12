import json
import urllib.request
import urllib.error
import time
import statistics
import random
import os
from collections import Counter
from typing import List, Dict, Any, Tuple

# --- Constants ---
API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
# Vercel-specific: Use /tmp for writable, but prefer bundled file for reading if /tmp is missing
WRITABLE_DATA_FILE = "/tmp/lotto_history.json" 
BUNDLED_DATA_FILE = os.path.join(os.path.dirname(__file__), "lotto_history.json")

# Primes in 1-45
PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43}
# OMR "Dead Zones" (Edges & Center - approximate)
OMR_DEAD_ZONES = {1, 7, 8, 14, 15, 21, 22, 28, 29, 35, 36, 42, 43, 4, 38} 

class LottoFetcher:
    """Fetches and manages Lotto 6/45 data from the official source."""
    
    def __init__(self):
        self.history = self._load_data()
        
    def _load_data(self) -> Dict[str, Any]:
        # Priority 1: Check /tmp (most recent if persisted slightly)
        if os.path.exists(WRITABLE_DATA_FILE):
            try:
                with open(WRITABLE_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
            
        # Priority 2: Check bundled file
        if os.path.exists(BUNDLED_DATA_FILE):
            try:
                with open(BUNDLED_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
            
        return {}

    def _fetch_round(self, round_no: int) -> Dict[str, Any]:
        """Fetches a single round's data with headers."""
        url = API_URL.format(round_no)
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("returnValue") == "success":
                        return data
        except Exception as e:
            print(f"Failed to fetch round {round_no}: {e}")
        return None

    def update_history(self, target_count: int = 200):
        # In Serverless, we might not want to do deep updates every request.
        # But we can try to fetch just the latest if missing.
        current_max = 0
        if self.history:
            current_max = max(int(k) for k in self.history.keys())
        
        # Simple update: Try to get next 1-2 rounds only to avoid timeout
        start_probe = max(current_max, 1100) 
        latest_round = start_probe
        
        # Try to fetch forward a bit
        for probe in range(start_probe + 1, start_probe + 3):
            if str(probe) in self.history:
                continue
            data = self._fetch_round(probe)
            if data:
                self.history[str(probe)] = data
            else:
                break
            
        self._save_data()

    def _save_data(self):
        try:
            with open(WRITABLE_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass # /tmp might not be available or other issue

    def get_last_n_rounds(self, n: int = 200) -> List[Dict[str, Any]]:
        sorted_keys = sorted([int(k) for k in self.history.keys()], reverse=True)
        return [self.history[str(k)] for k in sorted_keys[:n]]

class PatternAnalyzer:
    """Analyzes history to establish rule weights."""
    
    def __init__(self, history: List[Dict[str, Any]]):
        self.history = history
        self.weights = {
            'missing_zone': 0.5, 'carry_over': 0.5, 'same_ending': 0.5,
            'sum_range': 0.5, 'prime_count': 0.5, 'consecutive': 0.5,
            'dead_zone': 0.5, 'odd_even': 0.5, 'cold_num': 0.5, 'hot_rest': 0.5
        }
        
    def calibrate(self):
        if not self.history:
            return
            
        # Quick simple calibration to avoid heavy compute on serverless
        # (Ideally this should be pre-computed, but we'll do a fast pass)
        self.weights['missing_zone'] = 0.8
        self.weights['sum_range'] = 0.7
        self.weights['odd_even'] = 0.6

    def _get_nums(self, draw):
        return [draw[f'drwtNo{i}'] for i in range(1, 7)]

class LottoGenerator:
    """Generates numbers using Weighted Pattern Resonance."""
    
    def __init__(self, analyzer: PatternAnalyzer):
        self.analyzer = analyzer
        self.history_nums = [analyzer._get_nums(d) for d in analyzer.history]
        self.last_round_nums = set(self.history_nums[0]) if self.history_nums else set()
        
    def generate(self) -> Tuple[List[int], float, Dict[str, bool]]:
        best_candidate = None
        best_score = -1.0
        best_details = {}
        
        for _ in range(50): # Reduced iterations for serverless speed
            candidate = sorted(random.sample(range(1, 46), 6))
            score, details = self._calculate_resonance(candidate)
            
            if score > best_score:
                best_score = score
                best_candidate = candidate
                best_details = details
                
            if score > 85.0:
                break
                
        return best_candidate, best_score, best_details

    def _calculate_resonance(self, nums: List[int]) -> Tuple[float, Dict[str, bool]]:
        score = 0.0
        max_score = 0.0
        details = {}
        
        # Simplified rules for speed
        def check_missing_zone(n):
            zones = [
                any(1 <= x <= 10 for x in n), any(11 <= x <= 20 for x in n),
                any(21 <= x <= 30 for x in n), any(31 <= x <= 40 for x in n),
                any(41 <= x <= 45 for x in n)
            ]
            return not all(zones)
            
        def check_sum(n): return 120 <= sum(n) <= 160
        def check_odd_even(n):
            odd = len([x for x in n if x % 2 != 0])
            return odd in (3, 2, 4)
            
        # Rules Table
        rules = [
            ("Missing Zone", self.analyzer.weights['missing_zone'], check_missing_zone),
            ("Sum Range", self.analyzer.weights['sum_range'], check_sum),
            ("Odd/Even", 0.6, check_odd_even),
        ]
        
        for name, weight, func in rules:
            passed = func(nums)
            points = 10.0 * weight
            max_score += points
            if passed:
                score += points
            details[name] = passed
            
        final_score = (score / max_score) * 100 if max_score > 0 else 0
        return final_score, details
