"""
Korector - Modern Korean Spell Checker (Improved passportKey persistence)
v1.0.6.4
"""

import requests
import json
import re
import time
import sys
import platform
import random
from collections import Counter
from typing import Dict, Optional, Callable, Tuple, List
from functools import lru_cache
import concurrent.futures
import logging
import configparser
from pathlib import Path

try:
    import ua_parser.uap
    UA_PARSER_AVAILABLE = True
except ImportError:
    UA_PARSER_AVAILABLE = False

__version__ = "1.0.6.4"
__author__ = "ovin"

# User-Agent pool
PLATFORM_UA_POOL = {
    'linux': [
        'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ],
    'windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    ],
    'darwin': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0',
    ],
    'iphone': [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
    ],
    'ipad': [
        'Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
    ],
}


class NaverSpellChecker:
    """Naver Spell Checker API client – with passportKey persistence for library usage"""

    def __init__(self, verbose: bool = False):
        self.base_url = "https://ts-proxy.naver.com/ocontent/util/SpellerProxy"
        self.search_url = "https://search.naver.com/search.naver"
        self.passport_key = None
        self.session = requests.Session()
        self.verbose = verbose

        self.logger = logging.getLogger("korector")
        self.logger.setLevel(logging.INFO if verbose else logging.WARNING)

        # 저장 경로: 플랫폼에 따라 안정적으로 동작
        self.passport_key_path = Path.home() / ".korector_passport.ini"

        self.platform = self._detect_platform()
        self.current_ua_index = 0
        self._update_headers()

        # 저장된 키 로드
        self._load_passport_key()

    # --------------------------
    # 플랫폼 및 UA
    # --------------------------
    def _detect_platform(self) -> str:
        sys_platform = sys.platform.lower()
        machine = platform.machine().lower()

        if "iphone" in machine:
            return "iphone"
        if "ipad" in machine:
            return "ipad"
        if "darwin" in sys_platform:
            return "darwin"
        if "win" in sys_platform:
            return "windows"
        return "linux"

    def _get_platform_user_agent(self) -> str:
        uas = PLATFORM_UA_POOL.get(self.platform, PLATFORM_UA_POOL["linux"])
        ua = uas[self.current_ua_index % len(uas)]
        self.current_ua_index += 1
        return ua

    def _update_headers(self):
        ua_string = self._get_platform_user_agent()

        headers = {
            "User-Agent": ua_string,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

        self.session.headers.update(headers)

    # --------------------------
    # passportKey 저장·로드
    # --------------------------

    def _load_passport_key(self):
        """동일 장비 내 재사용을 위해 저장된 key 읽기"""
        if not self.passport_key_path.exists():
            return False

        config = configparser.ConfigParser()
        try:
            config.read(self.passport_key_path, encoding="utf-8")
            key = config.get("auth", "passport_key", fallback=None)

            if key and self._validate_passport_key(key):
                self.passport_key = key
                if self.verbose:
                    self.logger.info("🔑 Stored passportKey loaded.")
                return True
        except Exception:
            return False

        return False

    def _save_passport_key(self, key: str):
        """발급된 passportKey 로컬 저장"""
        try:
            config = configparser.ConfigParser()
            config["auth"] = {
                "passport_key": key,
                "timestamp": str(int(time.time()))
            }
            with open(self.passport_key_path, "w", encoding="utf-8") as f:
                config.write(f)
            if self.verbose:
                self.logger.info("💾 passportKey saved.")
        except Exception as e:
            if self.verbose:
                self.logger.warning(f"Failed to save passportKey: {e}")

    # --------------------------
    # Key refresh logic
    # --------------------------

    @lru_cache(maxsize=1)
    def _get_key_pattern(self) -> str:
        return r'checker:\s*"https://ts-proxy\.naver\.com/ocontent/util/SpellerProxy\?passportKey=([a-f0-9]{40})"'

    def _validate_passport_key(self, key: str) -> bool:
        return bool(key and re.match(r"^[a-f0-9]{40}$", key))

    def _refresh_passport_key(self) -> bool:
        """네이버에서 새로운 passportKey 발급"""
        try:
            self._update_headers()

            params = {"where": "nexearch", "query": "네이버 맞춤법 검사기"}

            response = self.session.get(
                self.search_url,
                params=params,
                headers={"Referer": "https://www.naver.com/"},
                timeout=15,
            )

            if response.status_code != 200:
                return False

            html_text = response.text
            match = re.search(self._get_key_pattern(), html_text)

            # pattern 방식
            if match:
                key = match.group(1)
                if self._validate_passport_key(key):
                    self.passport_key = key
                    self._save_passport_key(key)
                    return True

            # fallback: frequency 방식
            all_hex = re.findall(r"\b([a-f0-9]{40})\b", html_text)
            if all_hex:
                key = Counter(all_hex).most_common(1)[0][0]
                if self._validate_passport_key(key):
                    self.passport_key = key
                    self._save_passport_key(key)
                    return True

            return False

        except Exception:
            return False

    # --------------------------
    # Split text
    # --------------------------
    def _split_into_chunks(self, text: str, max_size: int = 450) -> List[str]:
        sentence_endings = r'[.!?\n]'
        sentences = re.split(f'({sentence_endings})', text)

        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            full_sentences.append(sentences[i] + sentences[i + 1])
        if len(sentences) % 2 == 1:
            full_sentences.append(sentences[-1])

        chunks = []
        current_chunk = ""

        for sentence in full_sentences:
            s = sentence.strip()
            if not s:
                continue

            if len(s) > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                for i in range(0, len(s), max_size):
                    chunks.append(s[i:i + max_size])
                continue

            if len(current_chunk) + len(s) > max_size:
                chunks.append(current_chunk)
                current_chunk = s
            else:
                current_chunk = s if not current_chunk else current_chunk + " " + s

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # --------------------------
    # Main spell check logic
    # --------------------------

    def check(self, text: str, retry=True, auto_split=True,
              progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        text = text.strip()
        if not text:
            return {
                "success": False,
                "original": text,
                "corrected": text,
                "error": "Empty text"
            }

        if auto_split and len(text) > 450:
            return self._check_parallel(text, progress_callback=progress_callback)

        return self._check_single(text, retry=retry)

    def _check_single(self, text: str, retry=True) -> Dict:
        start = time.time()

        # 1) 저장된 key 우선 사용
        if not self.passport_key:
            self._load_passport_key()

        # 2) 그래도 없다면 최초 발급
        if not self.passport_key:
            if not self._refresh_passport_key():
                return {
                    "success": False,
                    "original": text,
                    "corrected": text,
                    "error": "Failed to obtain passportKey",
                    "time": time.time() - start
                }

        timestamp = str(int(time.time() * 1000))
        callback = f"jQuery{timestamp}"

        params = {
            "passportKey": self.passport_key,
            "_callback": callback,
            "q": text,
            "where": "nexearch",
            "color_blindness": "0",
            "_": timestamp
        }

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                headers={"Referer": "https://search.naver.com/"},
                timeout=10,
            )

            # passportKey 만료 → 갱신 후 재시도
            if response.status_code in [401, 403] and retry:
                if self._refresh_passport_key():
                    time.sleep(0.2)
                    return self._check_single(text, retry=False)

            if response.status_code != 200:
                return {
                    "success": False,
                    "original": text,
                    "corrected": text,
                    "error": f"HTTP {response.status_code}",
                    "time": time.time() - start
                }

            json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
            if not json_match:
                if retry and self._refresh_passport_key():
                    return self._check_single(text, retry=False)
                return {
                    "success": False,
                    "original": text,
                    "corrected": text,
                    "error": "JSON parse failed",
                    "time": time.time() - start
                }

            data = json.loads(json_match.group())
            result = data.get("message", {}).get("result", {})

            corrected = result.get("notag_html", text)
            has_error = (text != corrected)

            return {
                "success": True,
                "original": text,
                "corrected": corrected,
                "html": result.get("html", ""),
                "origin_html": result.get("origin_html", ""),
                "error_count": result.get("errata_count", 0),
                "has_error": has_error,
                "time": time.time() - start
            }

        except Exception as e:
            return {
                "success": False,
                "original": text,
                "corrected": text,
                "error": str(e),
                "time": time.time() - start
            }

    # --------------------------

    def _check_parallel(self, text: str, chunk_size=450, max_workers=3,
                        progress_callback=None) -> Dict:
        start = time.time()

        chunks = self._split_into_chunks(text, chunk_size)
        total = len(chunks)

        indexed = list(enumerate(chunks))
        results = []

        def task(item):
            idx, chunk = item
            r = self._check_single(chunk)
            if progress_callback:
                progress_callback(idx + 1, total)
            return (idx, r)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exe:
            futures = [exe.submit(task, item) for item in indexed]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        results.sort(key=lambda x: x[0])

        corrected_parts = []
        html_parts = []
        origin_parts = []
        total_errors = 0
        failed = 0

        for idx, r in results:
            if r["success"]:
                corrected_parts.append(r["corrected"])
                html_parts.append(r.get("html", ""))
                origin_parts.append(r.get("origin_html", ""))
                total_errors += r.get("error_count", 0)
            else:
                corrected_parts.append(r["original"])
                html_parts.append(r["original"])
                origin_parts.append(r["original"])
                failed += 1

        return {
            "success": failed < total,
            "original": text,
            "corrected": " ".join(corrected_parts),
            "html": " ".join(html_parts),
            "origin_html": " ".join(origin_parts),
            "total_errors": total_errors,
            "has_error": (text != " ".join(corrected_parts)),
            "total_chunks": total,
            "failed_chunks": failed,
            "time": time.time() - start,
        }

    # --------------------------

    def health_check(self) -> Dict:
        if self.passport_key is None:
            self._load_passport_key()

        if self.passport_key is None:
            self._refresh_passport_key()

        test = self._check_single("안녕 하세요")
        if test["success"]:
            return {
                "status": "ok",
                "corrected": test["corrected"],
                "error_count": test["error_count"],
                "time": test["time"],
            }

        return {
            "status": "error",
            "message": test.get("error", "Unknown"),
        }

    def __del__(self):
        try:
            self.session.close()
        except:
            pass
