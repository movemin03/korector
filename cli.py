#!/usr/bin/env python3
"""
Korector CLI - Command Line Interface
"""

import argparse
import json
import sys
from korector import NaverSpellChecker

def main():
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
  korector "안녕 하세요"
  korector --health-check
  korector -f input.txt -o output.txt
  korector "마시면서배우는 수울게임" --verbose
        """
    )

    parser.add_argument('text', nargs='?', help='검사할 텍스트')
    parser.add_argument('-f', '--file', help='입력 파일 경로')
    parser.add_argument('-o', '--output', help='출력 파일 경로')
    parser.add_argument('--health-check', action='store_true', help='API 상태 확인')
    parser.add_argument('-v', '--verbose', action='store_true', help='상세 출력')
    parser.add_argument('--version', action='version', version=f'Korector {__import__("korector").__version__}')

    args = parser.parse_args()
    checker = NaverSpellChecker(verbose=args.verbose)

    if args.health_check:
        result = checker.health_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result['status'] == 'ok' else 1)

    if args.file:
        try:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(args.file, 'r', encoding='cp949') as f:
                    text = f.read()
        except Exception as e:
            print(f"파일 읽기 오류: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        sys.exit(0)

    # 진행 상황 콜백 (CLI 전용)
    def progress_callback(current: int, total: int):
        print(f"[{current}/{total}] 처리 중...")

    result = checker.check(text, progress_callback=progress_callback if args.verbose else None)

    if not result['success']:
        print(f"오류: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

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
        print(result['original'][:1000] + "..." if len(result['original']) > 1000 else result['original'])

        print(f"\n{'=' * 60}")
        print("교정:")
        print('=' * 60)
        print(result['corrected'][:1000] + "..." if len(result['corrected']) > 1000 else result['corrected'])

        if result.get('html'):
            print(f"\n{'=' * 60}")
            print("HTML (오류 표시):")
            print('=' * 60)
            print(result['html'][:1000] + "..." if len(result['html']) > 1000 else result['html'])

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result['corrected'])
            print(f"\n저장 완료: {args.output}")
        except Exception as e:
            print(f"파일 저장 오류: {e}", file=sys.stderr)
            sys.exit(1)
    elif not args.verbose:
        print(f"\n{'=' * 60}")
        print("결과:")
        print('=' * 60)
        print(result['corrected'])

    sys.exit(0)


if __name__ == "__main__":
    main()
