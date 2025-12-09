"""
Korector - Modern Korean Spell Checker
A simple and optimized Python library for Korean spell checking using Naver's API.
"""

import requests
import json
import re
import time
from collections import Counter
from typing import Dict, Optional, Callable, Tuple, List
from functools import lru_cache
import concurrent.futures
import logging

__version__ = "1.0.5"
__author__ = "ovin"


class NaverSpellChecker:
    """Naver Spell Checker API client - Silent by default"""

    def __init__(self, verbose: bool = False):
        self.base_url = "https://ts-proxy.naver.com/ocontent/util/SpellerProxy"
        self.search_url = "https://search.naver.com/search.naver"
        self.passport_key = None
        self.session = requests.Session()
        self.verbose = verbose
        self.logger = logging.getLogger('korector')
        self.logger.setLevel(logging.INFO if verbose else logging.WARNING)

        # 기본 헤더
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })

    def __del__(self):
        """세션 정리"""
        try:
            self.session.close()
        except:
            pass

    @lru_cache(maxsize=1)
    def _get_key_pattern(self) -> str:
        return r'checker:\s*"https://ts-proxy\.naver\.com/ocontent/util/SpellerProxy\?passportKey=([a-f0-9]{40})"'

    def _validate_passport_key(self, key: str) -> bool:
        if not key or len(key) != 40:
            return False
        return bool(re.match(r'^[a-f0-9]{40}$', key))

    def _refresh_passport_key(self) -> bool:
        try:
            params = {'where': 'nexearch', 'query': '네이버 맞춤법 검사기'}
            response = self.session.get(self.search_url, params=params, timeout=15)

            if response.status_code != 200:
                return False

            html_text = response.text
            pattern = self._get_key_pattern()
            match = re.search(pattern, html_text)

            if match:
                key = match.group(1)
                if self._validate_passport_key(key):
                    self.passport_key = key
                    return True

            all_hex = re.findall(r'\b([a-f0-9]{40})\b', html_text)
            if all_hex:
                key = Counter(all_hex).most_common(1)[0][0]
                if self._validate_passport_key(key):
                    self.passport_key = key
                    return True

            return False
        except Exception:
            return False

    def _split_into_chunks(self, text: str, max_size: int = 450) -> List[str]:
        """텍스트를 문장 단위로 똑똑하게 분할"""
        sentence_endings = r'[.!?\n]'
        sentences = re.split(f'({sentence_endings})', text)

        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                full_sentences.append(sentences[i] + sentences[i + 1])
            else:
                full_sentences.append(sentences[i])

        if len(sentences) % 2 == 1 and sentences[-1]:
            full_sentences.append(sentences[-1])

        chunks = []
        current_chunk = ""

        for sentence in full_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            potential_size = len(current_chunk) + len(sentence)

            if len(sentence) > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                for i in range(0, len(sentence), max_size):
                    chunks.append(sentence[i:i + max_size])
                continue

            if potential_size > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def check(self,
              text: str,
              retry: bool = True,
              auto_split: bool = True,
              progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """맞춤법 검사 - 조용한 라이브러리"""
        text = text.strip()
        if not text:
            return {
                'success': False, 'original': text, 'corrected': text,
                'error_count': 0, 'has_error': False, 'error': 'Empty text'
            }

        if auto_split and len(text) > 450:
            return self._check_parallel(text, progress_callback=progress_callback)

        return self._check_single(text, retry)

    def _check_single(self, text: str, retry: bool = True) -> Dict:
        """단일 요청으로 검사"""
        start_time = time.time()

        if not self.passport_key:
            if not self._refresh_passport_key():
                return {
                    'success': False, 'original': text, 'corrected': text,
                    'error_count': 0, 'has_error': False,
                    'time': time.time() - start_time, 'error': 'Failed to obtain passportKey'
                }

        timestamp = str(int(time.time() * 1000))
        callback = f"jQuery{timestamp}"

        params = {
            'passportKey': self.passport_key, '_callback': callback, 'q': text,
            'where': 'nexearch', 'color_blindness': '0', '_': timestamp
        }
        headers = {'Referer': 'https://search.naver.com/', 'Accept': '*/*'}

        try:
            response = self.session.get(self.base_url, params=params, headers=headers, timeout=10)

            if response.status_code in [401, 403] and retry:
                if self._refresh_passport_key():
                    time.sleep(0.3)
                    return self._check_single(text, retry=False)

            if response.status_code != 200:
                return {
                    'success': False, 'original': text, 'corrected': text,
                    'error_count': 0, 'has_error': False,
                    'time': time.time() - start_time, 'error': f"HTTP {response.status_code}"
                }

            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not json_match:
                if retry and self._refresh_passport_key():
                    time.sleep(0.3)
                    return self._check_single(text, retry=False)
                return {
                    'success': False, 'original': text, 'corrected': text,
                    'error_count': 0, 'has_error': False,
                    'time': time.time() - start_time, 'error': 'JSON parsing failed'
                }

            data = json.loads(json_match.group())
            result = data.get('message', {}).get('result', {})

            corrected = result.get('notag_html', text)
            has_error = (text != corrected)

            return {
                'success': True, 'original': text, 'corrected': corrected,
                'html': result.get('html', ''), 'origin_html': result.get('origin_html', ''),
                'error_count': result.get('errata_count', 0), 'has_error': has_error,
                'time': time.time() - start_time
            }

        except Exception as e:
            return {
                'success': False, 'original': text, 'corrected': text,
                'error_count': 0, 'has_error': False,
                'time': time.time() - start_time, 'error': str(e)
            }

    def _check_parallel(self, text: str,
                       chunk_size: int = 450,
                       max_workers: int = 3,
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """긴 텍스트 병렬 처리"""
        start_time = time.time()
        chunks = self._split_into_chunks(text, chunk_size)
        total_chunks = len(chunks)

        if self.verbose or progress_callback:
            self.logger.info(f"총 {total_chunks}개 청크로 병렬 처리 시작")

        indexed_chunks = [(i, chunk) for i, chunk in enumerate(chunks)]

        def process_chunk(item: Tuple[int, str]) -> Tuple[int, dict]:
            index, chunk = item
            result = self._check_single(chunk)
            if self.verbose or progress_callback:
                self.logger.info(f"청크 {index + 1}/{total_chunks} 완료 ({result['time']:.2f}초)")
                if progress_callback:
                    progress_callback(index + 1, total_chunks)
            return (index, result)

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_chunk, chunk) for chunk in indexed_chunks]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        results.sort(key=lambda x: x[0])

        corrected_parts = []
        html_parts = []
        origin_html_parts = []
        total_errors = 0
        failed_chunks = 0

        for index, result in results:
            if result['success']:
                corrected_parts.append(result['corrected'])
                html_parts.append(result.get('html', ''))
                origin_html_parts.append(result.get('origin_html', ''))
                total_errors += result['error_count']
            else:
                corrected_parts.append(result['original'])
                html_parts.append(result['original'])
                origin_html_parts.append(result['original'])
                failed_chunks += 1

        corrected_text = ' '.join(corrected_parts)

        return {
            'success': failed_chunks < total_chunks,
            'original': text,
            'corrected': corrected_text,
            'html': ' '.join(html_parts),
            'origin_html': ' '.join(origin_html_parts),
            'total_errors': total_errors,
            'has_error': (text != corrected_text),
            'total_chunks': total_chunks,
            'failed_chunks': failed_chunks,
            'time': time.time() - start_time
        }

    def health_check(self) -> Dict:
        """API 상태 확인"""
        if not self.passport_key:
            if not self._refresh_passport_key():
                return {'status': 'error', 'message': 'Failed to obtain passportKey'}

        result = self._check_single("안녕 하세요")
        return {
            'status': 'ok' if result['success'] else 'error',
            'test_result': {
                'text': "안녕 하세요",
                'corrected': result['corrected'],
                'error_count': result['error_count'],
                'has_error': result['has_error'],
                'time': result['time']
            }
        }
