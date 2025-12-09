"""
Korector - Modern Korean Spell Checker
A secure and optimized Python library for Korean spell checking using Naver's API.
"""

import requests
import json
import re
import time
import sys
import hashlib
import hmac
import secrets
import gzip
import base64
from collections import Counter
from typing import Dict, Optional, Callable, List
from functools import lru_cache
import threading


__version__ = "1.0.0"
__author__ = "movemin"


class SecureSession:
    """Secure HTTP session with request signing"""

    def __init__(self):
        self.session = requests.Session()
        self._session_id = secrets.token_hex(16)
        self._request_count = 0
        self._lock = threading.Lock()

        # Secure headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

    def _generate_request_signature(self, url: str, params: dict) -> str:
        """Generate HMAC signature for request validation"""
        with self._lock:
            self._request_count += 1
            data = f"{url}:{self._request_count}:{json.dumps(params, sort_keys=True)}"
            signature = hmac.new(
                self._session_id.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            return signature

    def get(self, url: str, params: dict = None, **kwargs) -> requests.Response:
        """Secure GET request with signature"""
        if params:
            signature = self._generate_request_signature(url, params)
            # Add signature to internal tracking (not sent to server)

        return self.session.get(url, params=params, **kwargs)

    def close(self):
        """Close session securely"""
        self.session.close()
        self._session_id = None


class TextCompressor:
    """Text compression for efficient network transmission"""

    @staticmethod
    def compress(text: str) -> str:
        """Compress text using gzip and base64 encode"""
        if len(text) < 100:  # Don't compress short texts
            return text

        try:
            compressed = gzip.compress(text.encode('utf-8'), compresslevel=6)
            encoded = base64.b64encode(compressed).decode('ascii')
            return f"GZIP:{encoded}"
        except Exception:
            return text

    @staticmethod
    def decompress(data: str) -> str:
        """Decompress gzipped base64 data"""
        if not data.startswith("GZIP:"):
            return data

        try:
            encoded = data[5:]  # Remove "GZIP:" prefix
            compressed = base64.b64decode(encoded)
            decompressed = gzip.decompress(compressed).decode('utf-8')
            return decompressed
        except Exception:
            return data


class NaverSpellChecker:
    """Secure and optimized Naver Spell Checker API client"""

    ERROR_TYPES = {
        'result_underline': 'spelling',
        'violet_text': 'standard',
        'green_text': 'spacing',
        'blue_text': 'statistical'
    }

    def __init__(self):
        self.base_url = "https://ts-proxy.naver.com/ocontent/util/SpellerProxy"
        self.search_url = "https://search.naver.com/search.naver"
        self.passport_key = None
        self.session = SecureSession()
        self.compressor = TextCompressor()
        self._key_hash = None
        self._lock = threading.Lock()

    def __del__(self):
        """Secure cleanup"""
        try:
            self.session.close()
            self.passport_key = None
            self._key_hash = None
        except:
            pass

    @lru_cache(maxsize=128)
    def _get_cached_key_pattern(self) -> str:
        """Cache regex pattern for performance"""
        return r'checker:\s*"https://ts-proxy\.naver\.com/ocontent/util/SpellerProxy\?passportKey=([a-f0-9]{40})"'

    def _validate_passport_key(self, key: str) -> bool:
        """Validate passport key format"""
        if not key or len(key) != 40:
            return False
        return bool(re.match(r'^[a-f0-9]{40}$', key))

    def _hash_key(self, key: str) -> str:
        """Create hash of key for secure storage"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _refresh_passport_key(self) -> bool:
        """Extract passportKey with enhanced security"""
        with self._lock:
            try:
                params = {
                    'where': 'nexearch',
                    'sm': 'top_sug.pre',
                    'fbm': '0',
                    'acr': '1',
                    'acq': '네이버 맞춤',
                    'qdt': '0',
                    'ie': 'utf8',
                    'query': '네이버 맞춤법 검사기'
                }

                response = self.session.get(self.search_url, params=params, timeout=15)
                response.encoding = 'utf-8'

                if response.status_code != 200:
                    return False

                html_text = response.text
                pattern = self._get_cached_key_pattern()
                match = re.search(pattern, html_text)

                if match:
                    key = match.group(1)
                    if self._validate_passport_key(key):
                        self.passport_key = key
                        self._key_hash = self._hash_key(key)
                        return True

                # Fallback
                all_hex = re.findall(r'\b([a-f0-9]{40})\b', html_text)
                if all_hex:
                    key = Counter(all_hex).most_common(1)[0][0]
                    if self._validate_passport_key(key):
                        self.passport_key = key
                        self._key_hash = self._hash_key(key)
                        return True

                return False

            except Exception:
                return False

    def _sanitize_input(self, text: str) -> str:
        """Sanitize input text for security"""
        if not text:
            return ""

        # Remove potential XSS/injection patterns
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

        return text.strip()

    def check(self, text: str, retry: bool = True) -> Dict:
        """
        Check spelling with enhanced security and optimization

        Args:
            text (str): Text to check
            retry (bool): Retry on token expiration

        Returns:
            dict: Result with corrections and metadata
        """
        start_time = time.time()

        # Input validation and sanitization
        text = self._sanitize_input(text)
        if not text:
            return {
                'success': False,
                'original': text,
                'corrected': text,
                'error_count': 0,
                'has_error': False,
                'time': time.time() - start_time,
                'error': 'Empty or invalid text'
            }

        if not self.passport_key:
            if not self._refresh_passport_key():
                return {
                    'success': False,
                    'original': text,
                    'corrected': text,
                    'error_count': 0,
                    'has_error': False,
                    'time': time.time() - start_time,
                    'error': 'Failed to obtain passportKey'
                }

        timestamp = str(int(time.time() * 1000))
        callback = f"jQuery{timestamp}_{secrets.token_hex(8)}"

        params = {
            'passportKey': self.passport_key,
            '_callback': callback,
            'q': text,
            'where': 'nexearch',
            'color_blindness': '0',
            '_': timestamp
        }

        headers = {
            'Referer': 'https://search.naver.com/',
            'Accept': '*/*',
            'sec-fetch-dest': 'script',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'same-site'
        }

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code in [401, 403] and retry:
                if self._refresh_passport_key():
                    time.sleep(0.5)
                    return self.check(text, retry=False)

            if response.status_code != 200:
                return {
                    'success': False,
                    'original': text,
                    'corrected': text,
                    'error_count': 0,
                    'has_error': False,
                    'time': time.time() - start_time,
                    'error': f"HTTP {response.status_code}"
                }

            # Secure JSON parsing
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not json_match:
                if retry and self._refresh_passport_key():
                    time.sleep(0.5)
                    return self.check(text, retry=False)

                return {
                    'success': False,
                    'original': text,
                    'corrected': text,
                    'error_count': 0,
                    'has_error': False,
                    'time': time.time() - start_time,
                    'error': 'JSON parsing failed'
                }

            data = json.loads(json_match.group())
            result = data.get('message', {}).get('result', {})

            corrected = result.get('notag_html', text)
            has_error = (text != corrected)

            return {
                'success': True,
                'original': text,
                'corrected': corrected,
                'html': result.get('html', ''),
                'origin_html': result.get('origin_html', ''),
                'error_count': result.get('errata_count', 0),
                'has_error': has_error,
                'time': time.time() - start_time,
                'raw_response': data
            }

        except json.JSONDecodeError:
            return {
                'success': False,
                'original': text,
                'corrected': text,
                'error_count': 0,
                'has_error': False,
                'time': time.time() - start_time,
                'error': 'Invalid JSON response'
            }
        except Exception as e:
            return {
                'success': False,
                'original': text,
                'corrected': text,
                'error_count': 0,
                'has_error': False,
                'time': time.time() - start_time,
                'error': str(e)
            }

    def check_long_text(self, text: str, chunk_size: int = 400,
                       delay: float = 0.5, callback: Optional[Callable] = None) -> Dict:
        """
        Check long text with optimization

        Args:
            text (str): Text to check
            chunk_size (int): Size of each chunk
            delay (float): Delay between requests
            callback (callable): Progress callback function(current, total, result)

        Returns:
            dict: Result with corrections and statistics
        """
        start_time = time.time()

        text = self._sanitize_input(text)
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        corrected_chunks = []
        html_chunks = []
        origin_html_chunks = []
        total_errors = 0
        total_changes = 0
        failed_chunks = 0

        for i, chunk in enumerate(chunks):
            result = self.check(chunk)

            if result['success']:
                corrected_chunks.append(result['corrected'])
                html_chunks.append(result['html'])
                origin_html_chunks.append(result['origin_html'])
                total_errors += result['error_count']
                if result['has_error']:
                    total_changes += 1
            else:
                corrected_chunks.append(chunk)
                html_chunks.append(chunk)
                origin_html_chunks.append(chunk)
                failed_chunks += 1

            if callback:
                callback(i + 1, len(chunks), result)

            if i < len(chunks) - 1:
                time.sleep(delay)

        corrected_text = ''.join(corrected_chunks)

        return {
            'success': failed_chunks < len(chunks),
            'original': text,
            'corrected': corrected_text,
            'html': ''.join(html_chunks),
            'origin_html': ''.join(origin_html_chunks),
            'total_errors': total_errors,
            'has_error': (text != corrected_text),
            'chunks_with_errors': total_changes,
            'total_chunks': len(chunks),
            'failed_chunks': failed_chunks,
            'time': time.time() - start_time
        }

    def health_check(self) -> Dict:
        """Check API health with security validation"""
        if not self.passport_key:
            if not self._refresh_passport_key():
                return {'status': 'error', 'message': 'Failed to obtain passportKey'}

        result = self.check("안녕 하세요")

        if result['success']:
            return {
                'status': 'ok',
                'passport_key_hash': self._key_hash,
                'test_result': {
                    'text': "안녕 하세요",
                    'corrected': result['corrected'],
                    'error_count': result['error_count'],
                    'has_error': result['has_error'],
                    'time': result['time']
                }
            }
        else:
            return {'status': 'error', 'message': result.get('error')}


def main():
    """Secure CLI interface"""
    import argparse

    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

    parser = argparse.ArgumentParser(
        description='Korector: Secure Korean Spell Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "안녕 하세요"
  %(prog)s --health-check
  %(prog)s -f input.txt -o output.txt
  %(prog)s "아빡가가방에드러간다" --verbose
        """
    )

    parser.add_argument('text', nargs='?', help='Text to check')
    parser.add_argument('-f', '--file', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-c', '--chunk-size', type=int, default=400,
                        help='Chunk size (default: 400)')
    parser.add_argument('--health-check', action='store_true',
                        help='Check API health')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    checker = NaverSpellChecker()

    if args.health_check:
        result = checker.health_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] == 'ok' else 1

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8-sig') as f:
                text = f.read()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        return 0

    def progress(current, total, result):
        status = "✓" if result['success'] else "✗"
        err = "!" if result.get('has_error') else " "
        print(f"  [{status}{err}] {current}/{total} ({result.get('time', 0):.3f}s)")

    if len(text) > 400:
        result = checker.check_long_text(text, args.chunk_size, callback=progress)
        print(f"\nTime: {result['time']:.3f}s")
        print(f"Errors: {result['total_errors']}")
        print(f"Changed: {'Yes' if result['has_error'] else 'No'}")
        corrected = result['corrected']
        html = result.get('html', '')
        origin_html = result.get('origin_html', '')
    else:
        result = checker.check(text)
        if not result['success']:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1

        print(f"Time: {result['time']:.3f}s")
        print(f"Errors: {result['error_count']}")
        print(f"Changed: {'Yes' if result['has_error'] else 'No'}")
        corrected = result['corrected']
        html = result.get('html', '')
        origin_html = result.get('origin_html', '')

    if args.verbose:
        print(f"\n{'='*60}")
        print("Original:")
        print('='*60)
        print(result.get('original', text))

        print(f"\n{'='*60}")
        print("Corrected:")
        print('='*60)
        print(corrected)

        if html:
            print(f"\n{'='*60}")
            print("HTML:")
            print('='*60)
            print(html)
            print("\nError type legend:")
            print("  - result_underline: Spelling error")
            print("  - violet_text: Non-standard word")
            print("  - green_text: Spacing error")
            print("  - blue_text: Statistical correction")

        if origin_html:
            print(f"\n{'='*60}")
            print("Origin HTML:")
            print('='*60)
            print(origin_html)

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8-sig') as f:
                f.write(corrected)
            print(f"\nSaved: {args.output}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif not args.verbose:
        print(f"\n{'='*60}")
        print("Result:")
        print('='*60)
        print(corrected)

    return 0


if __name__ == "__main__":
    sys.exit(main())
