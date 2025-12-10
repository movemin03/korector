#!/usr/bin/env python3
"""
Korector CLI - Command Line Interface (Enhanced passportKey persistence)
v1.0.6.4
"""

import argparse
import json
import sys
from korector import NaverSpellChecker


def main():
    # Windows UTF-8 처리
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Korector: Korean Spell Checker (passportKey persistence enabled)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  korector "안녕 하세요"
  korector --health-check
  korector -f input.txt -o output.txt
  korector "마시면서배우는 수울게임" --verbose
        """
    )

    parser.add_argument("text", nargs="?", help="검사할 텍스트")
    parser.add_argument("-f", "--file", help="입력 파일 경로")
    parser.add_argument("-o", "--output", help="출력 파일 경로")
    parser.add_argument("--health-check", action="store_true", help="API 상태 확인")
    parser.add_argument("-v", "--verbose", action="store_true", help="상세 출력")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Korector CLI {__import__('korector').__version__}"
    )

    args = parser.parse_args()

    # Korector 엔진 생성
    checker = NaverSpellChecker(verbose=args.verbose)

    # ------------------------------
    # 헬스 체크
    # ------------------------------
    if args.health_check:
        result = checker.health_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("status") == "ok":
            sys.exit(0)
        sys.exit(1)

    # ------------------------------
    # 입력 텍스트 로딩
    # ------------------------------
    if args.file:
        try:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(args.file, "r", encoding="cp949") as f:
                    text = f.read()
        except Exception as e:
            print(f"❌ 파일 읽기 오류: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.text:
        text = args.text
    else:
        parser.print_help()
        sys.exit(0)

    # ------------------------------
    # 진행률 콜백 함수
    # ------------------------------
    def progress_callback(current, total):
        print(f"[{current}/{total}] 처리중...")

    # ------------------------------
    # 맞춤법 검사 실행
    # ------------------------------
    result = checker.check(
        text,
        progress_callback=progress_callback if args.verbose else None
    )

    if not result.get("success", False):
        print(f"❌ 오류: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"\n⏱ 처리 시간: {result['time']:.3f}초")

    if "total_errors" in result:
        print(f"🔎 전체 오류 수: {result['total_errors']}")
        print(f"📦 병렬 처리 청크 수: {result['total_chunks']}")
    else:
        print(f"🔎 오류 수: {result['error_count']}")

    print(f"🔄 변경 여부: {'있음' if result['has_error'] else '없음'}")

    # ------------------------------
    # verbose 출력
    # ------------------------------
    if args.verbose:
        print("\n" + "=" * 60)
        print("원본:")
        print("=" * 60)
        print(result["original"][:1000] + "..." if len(result["original"]) > 1000 else result["original"])

        print("\n" + "=" * 60)
        print("교정 결과:")
        print("=" * 60)
        print(result["corrected"][:1000] + "..." if len(result["corrected"]) > 1000 else result["corrected"])

        if result.get("html"):
            print("\n" + "=" * 60)
            print("HTML 결과:")
            print("=" * 60)
            print(result["html"][:1000] + "..." if len(result["html"]) > 1000 else result["html"])

    # ------------------------------
    # 출력 저장
    # ------------------------------
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result["corrected"])
            print(f"\n💾 저장 완료: {args.output}")
        except Exception as e:
            print(f"❌ 저장 오류: {e}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------
    # 기본 출력
    # ------------------------------
    elif not args.verbose:
        print("\n" + "=" * 60)
        print("최종 결과:")
        print("=" * 60)
        print(result["corrected"])

    sys.exit(0)


if __name__ == "__main__":
    main()
