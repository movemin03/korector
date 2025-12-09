"""
Korector - Modern Korean Spell Checker
A simple and optimized Python library for Korean spell checking using Naver's API.
"""

import requests
import json
import re
import time
import sys
from collections import Counter
from typing import Dict, Optional, Callable, Tuple, List
from functools import lru_cache
import concurrent.futures

__version__ = "1.0.4"
__author__ = "movemin"


class NaverSpellChecker:
    """Naver Spell Checker API client"""

    def __init__(self):
        self.base_url = "https://ts-proxy.naver.com/ocontent/util/SpellerProxy"
        self.search_url = "https://search.naver.com/search.naver"
        self.passport_key = None
        self.session = requests.Session()

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
        """정규표현식 패턴 캐싱"""
        return r'checker:\s*"https://ts-proxy\.naver\.com/ocontent/util/SpellerProxy\?passportKey=([a-f0-9]{40})"'

    def _validate_passport_key(self, key: str) -> bool:
        """Passport Key 형식 검증"""
        if not key or len(key) != 40:
            return False
        return bool(re.match(r'^[a-f0-9]{40}$', key))

    def _refresh_passport_key(self) -> bool:
        """Passport Key 가져오기"""
        try:
            params = {
                'where': 'nexearch',
                'query': '네이버 맞춤법 검사기'
            }

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

            # 폴백: 빈도 분석
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
        """
        텍스트를 문장 단위로 똑똑하게 분할

        Args:
            text: 분할할 텍스트
            max_size: 최대 청크 크기

        Returns:
            분할된 청크 리스트
        """
        # 문장 종결 기호로 분할 (., !, ?, \n 등)
        sentence_endings = r'[.!?\n]'
        sentences = re.split(f'({sentence_endings})', text)

        # 종결 기호를 문장에 다시 붙이기
        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                full_sentences.append(sentences[i] + sentences[i + 1])
            else:
                full_sentences.append(sentences[i])

        # 마지막 문장이 종결 기호 없이 끝난 경우
        if len(sentences) % 2 == 1 and sentences[-1]:
            full_sentences.append(sentences[-1])

        # 청킹
        chunks = []
        current_chunk = ""

        for sentence in full_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 현재 청크에 추가했을 때 크기
            potential_size = len(current_chunk) + len(sentence)

            # 한 문장이 max_size를 넘는 경우 - 강제로 잘라야 함
            if len(sentence) > max_size:
                # 현재 청크가 있으면 먼저 저장
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # 긴 문장을 강제로 분할
                for i in range(0, len(sentence), max_size):
                    chunks.append(sentence[i:i + max_size])
                continue

            # max_size를 넘으면 현재 청크 저장하고 새로 시작
            if potential_size > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # 청크에 추가 (공백으로 구분)
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # 마지막 청크 저장
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def check(self, text: str, retry: bool = True, auto_split: bool = True) -> Dict:
        """
        맞춤법 검사 (자동으로 긴 텍스트 처리)

        Args:
            text (str): 검사할 텍스트
            retry (bool): 실패 시 재시도
            auto_split (bool): 긴 텍스트 자동 분할 처리

        Returns:
            dict: 검사 결과
        """
        text = text.strip()
        if not text:
            return {
                'success': False,
                'original': text,
                'corrected': text,
                'error_count': 0,
                'has_error': False,
                'error': 'Empty text'
            }

        # 긴 텍스트는 자동으로 분할 처리
        if auto_split and len(text) > 450:
            return self._check_parallel(text)

        # 짧은 텍스트는 단일 요청
        return self._check_single(text, retry)

    def _check_single(self, text: str, retry: bool = True) -> Dict:
        """단일 요청으로 검사"""
        start_time = time.time()

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
        callback = f"jQuery{timestamp}"

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
                    time.sleep(0.3)
                    return self._check_single(text, retry=False)

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

            # JSON 파싱
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not json_match:
                if retry and self._refresh_passport_key():
                    time.sleep(0.3)
                    return self._check_single(text, retry=False)

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
                'time': time.time() - start_time
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

    def _check_parallel(self, text: str, chunk_size: int = 450, max_workers: int = 3) -> Dict:
        """긴 텍스트를 병렬 처리 (문장 단위로 똑똑하게 분할)"""
        start_time = time.time()

        # 1. 텍스트를 문장 단위로 똑똑하게 분할
        chunks = self._split_into_chunks(text, chunk_size)

        print(f"총 {len(chunks)}개 청크로 분할하여 병렬 처리 시작...")

        # 청크 정보 출력 (디버깅용)
        for i, chunk in enumerate(chunks):
            print(f"  청크 {i+1}: {len(chunk)}자 (미리보기: {chunk[:50]}...)")

        # 2. 청크에 순서 번호 부여
        indexed_chunks = [(i, chunk) for i, chunk in enumerate(chunks)]

        # 3. 청크 처리 함수
        def process_chunk(item: Tuple[int, str]) -> Tuple[int, dict]:
            index, chunk = item
            result = self._check_single(chunk)
            if result['success']:
                print(f"  ✓ 청크 {index + 1}/{len(chunks)} 완료 ({result['time']:.2f}초, {len(chunk)}자)")
            else:
                print(f"  ✗ 청크 {index + 1}/{len(chunks)} 실패")
            return (index, result)

        # 4. 병렬 실행
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_chunk, chunk) for chunk in indexed_chunks]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # 5. 순서대로 정렬
        results.sort(key=lambda x: x[0])

        # 6. 결과 합치기
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

        # 공백으로 청크 연결 (문장 단위로 나눴으므로)
        corrected_text = ' '.join(corrected_parts)

        return {
            'success': failed_chunks < len(chunks),
            'original': text,
            'corrected': corrected_text,
            'html': ' '.join(html_parts),
            'origin_html': ' '.join(origin_html_parts),
            'total_errors': total_errors,
            'has_error': (text != corrected_text),
            'total_chunks': len(chunks),
            'failed_chunks': failed_chunks,
            'time': time.time() - start_time
        }

    def health_check(self) -> Dict:
        """API 상태 확인"""
        if not self.passport_key:
            if not self._refresh_passport_key():
                return {'status': 'error', 'message': 'Failed to obtain passportKey'}

        result = self._check_single("안녕 하세요")

        if result['success']:
            return {
                'status': 'ok',
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
    """CLI 인터페이스"""
    import argparse

    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

    parser = argparse.ArgumentParser(
        description='Korector: Korean Spell Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  %(prog)s "안녕 하세요"
  %(prog)s --health-check
  %(prog)s -f input.txt -o output.txt
  %(prog)s "마시면서배우는 수울게임" --verbose
        """
    )

    parser.add_argument('text', nargs='?', help='검사할 텍스트')
    parser.add_argument('-f', '--file', help='입력 파일 경로')
    parser.add_argument('-o', '--output', help='출력 파일 경로')
    parser.add_argument('--health-check', action='store_true',
                        help='API 상태 확인')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='상세 출력')
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
            # 인코딩 자동 처리
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(args.file, 'r', encoding='cp949') as f:
                    text = f.read()
        except Exception as e:
            print(f"파일 읽기 오류: {e}", file=sys.stderr)
            return 1
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        return 0

    # 자동으로 처리 (긴 텍스트는 자동 분할)
    result = checker.check(text)

    if not result['success']:
        print(f"오류: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    print(f"\n처리 시간: {result['time']:.3f}초")

    if 'total_errors' in result:
        print(f"전체 오류: {result['total_errors']}")
        print(f"처리 청크: {result['total_chunks']}")
    else:
        print(f"오류 개수: {result['error_count']}")

    print(f"변경 여부: {'있음' if result['has_error'] else '없음'}")

    if args.verbose:
        print(f"\n{'=' * 60}")
        print("원본:")
        print('=' * 60)
        print(result['original'])

        print(f"\n{'=' * 60}")
        print("교정:")
        print('=' * 60)
        print(result['corrected'])

        if result.get('html'):
            print(f"\n{'=' * 60}")
            print("HTML (오류 표시):")
            print('=' * 60)
            print(result['html'])

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result['corrected'])
            print(f"\n저장 완료: {args.output}")
        except Exception as e:
            print(f"파일 저장 오류: {e}", file=sys.stderr)
            return 1
    elif not args.verbose:
        print(f"\n{'=' * 60}")
        print("결과:")
        print('=' * 60)
        print(result['corrected'])

    return 0


if __name__ == "__main__":
    sys.exit(main())
