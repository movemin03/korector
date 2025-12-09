# Korector

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Korector**는 네이버 맞춤법 검사기를 이용한 파이썬용 한글 맞춤법/띄어쓰기 검사 라이브러리입니다.  토큰 자동 관리, 긴 텍스트 처리, 응답 시간 측정 등 기능을 강화했습니다.

---

## 특징

- 네이버 맞춤법 검사기를 이용한 한글 맞춤법/띄어쓰기 검사
- passportKey 자동 추출 및 갱신
- 긴 텍스트 자동 분할 처리 (chunk 단위)
- 요청당 응답 시간(`time`) 측정
- HTML 하이라이트 / 원본 HTML / 원본 응답(raw) 제공
- CLI(커맨드라인) 인터페이스 지원

---

## 설치

### pip로 설치 (예정)


pip install korector
text

### 소스에서 설치


- git clone https://github.com/movemin03/korector.git
- cd korector
- python setup.py install
- text

또는 `korector` 폴더를 그대로 자신의 프로젝트에 포함시켜 사용할 수도 있습니다.

---

## 필요한 라이브러리

- `requests`

---

## 기본 사용법


from korector import NaverSpellChecker
checker = NaverSpellChecker()
result = checker.check("안녕 하세요. 저는 한국인 입니다.")
print(result["corrected"]) # 교정된 문장
print(result["error_count"]) # 네이버 API 기준 오류 개수
print(result["has_error"]) # 실제 문장 변경 여부
print(result["time"]) # 응답 시간(초)
text

예상 반환값 형태:


{
"success": True,
"original": "안녕 하세요. 저는 한국인 입니다.",
"corrected": "안녕하세요. 저는 한국인입니다.",
"html": "<em class='green_text'>안녕하세요.</em> 저는 <em class='green_text'>한국인입니다.</em>",
"origin_html": "<span class='result_underline'>안녕 하세요.</span> 저는 <span class='result_underline'>한국인 입니다.</span>",
"error_count": 2,
"has_error": True,
"time": 0.15,
"raw_response": {...}
}
text

---

## 긴 텍스트 처리


text = "..." # 매우 긴 텍스트
def progress(current, total, result):
print(f"[{current}/{total}] {result['time']:.3f}s, changed={result['has_error']}")
checker = NaverSpellChecker()
result = checker.check_long_text(
text,
chunk_size=400,
delay=0.5,
callback=progress,
)
print("총 시간:", result["time"])
print("총 오류 개수:", result["total_errors"])
print("최종 문장 변경 여부:", result["has_error"])
text

`check_long_text()`의 반환값 예:


{
"success": True,
"original": "...",
"corrected": "...",
"html": "...",
"origin_html": "...",
"total_errors": 10,
"has_error": True,
"chunks_with_errors": 5,
"total_chunks": 8,
"failed_chunks": 0,
"time": 1.23
}
text

---

## CLI 사용법

설치 후에는 `korector`(또는 `korector-cli`) 명령으로 사용할 수 있습니다.


단일 문장 검사
$ korector "안녕 하세요"
Time: 0.143s
Errors: 1
Changed: Yes
============================================================
Result:
안녕하세요
파일 입력/출력
$ korector -f input.txt -o output.txt
상세 출력(HTML/원본 응답 등)
$ korector "아빡가가방에드러간다" --verbose
헬스 체크
$ korector --health-check
text

주요 옵션:

- `text` : 검사할 문장 (positional)
- `-f, --file` : 입력 파일 경로
- `-o, --output` : 교정된 결과 저장 파일 경로
- `-c, --chunk-size` : 긴 텍스트 분할 크기 (기본 400자)
- `--health-check` : API 상태 및 토큰 정상 여부 확인
- `-v, --verbose` : 원문/교정문/HTML/시간 등을 자세히 출력
- `--version` : Korector 버전 표시

---

## 반환값 필드 정리

### `check()` 결과

| Key           | Type  | 설명                              |
|---------------|-------|-----------------------------------|
| `success`     | bool  | 검사 성공 여부                    |
| `original`    | str   | 검사 전 문장                      |
| `corrected`   | str   | 교정된 문장(plain text)          |
| `html`        | str   | 하이라이트된 HTML                |
| `origin_html` | str   | 원본 밑줄 HTML                    |
| `error_count` | int   | 네이버 API에서 내려주는 오류 수  |
| `has_error`   | bool  | 원본과 교정 문장이 다른지 여부   |
| `time`        | float | 요청~응답까지 걸린 시간(초)      |
| `raw_response`| dict  | 네이버 API 원본 응답 JSON        |

### HTML 클래스와 의미

- `result_underline` : 맞춤법 오류
- `violet_text`      : 표준어 의심
- `green_text`       : 띄어쓰기 오류
- `blue_text`        : 통계적 교정

---

## 주의사항

- 이 라이브러리는 **네이버 한글 맞춤법 검사기**를 기반으로 동작합니다.
- 검사 결과 및 데이터에 대한 저작권과 책임은 **네이버 주식회사**에 있습니다.
- 상업적/대량 호출 시에는 트래픽·정책을 반드시 검토해야 합니다.
- 네이버 측 정책/응답 포맷 변경 시 라이브러리가 동작하지 않을 수 있습니다.
