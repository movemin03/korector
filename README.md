# Korector

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

**Korector**는 네이버 맞춤법 검사기를 이용한 파이썬용 한글 맞춤법/띄어쓰기 검사 라이브러리입니다.

passportKey 자동 관리, 긴 텍스트 처리, 응답 시간 측정, 보안 강화 등 다양한 기능을 제공합니다.

---

## ✨ 특징

- ✅ **네이버 맞춤법 검사기** 기반 정확한 한글 맞춤법/띄어쓰기 검사
- ✅ **자동 토큰 관리** - passportKey 자동 추출 및 갱신
- ✅ **긴 텍스트 지원** - 400자 이상 텍스트 자동 분할 처리
- ✅ **응답 시간 측정** - 모든 요청에 대한 정확한 시간 추적
- ✅ **보안 강화** - XSS/Injection 방어, HMAC 서명, 입력 검증
- ✅ **최적화** - LRU 캐싱, gzip 압축, 멀티스레드 안전
- ✅ **상세한 결과** - HTML 하이라이팅 및 원본 응답 포함
- ✅ **CLI 지원** - 커맨드라인에서 바로 사용 가능

---

## 📦 설치

### pip로 설치 (권장)

```
pip install korector
```

### GitHub에서 직접 설치

```
git clone https://github.com/movemin03/korector.git
cd korector
python setup.py install
```

### 필요한 라이브러리

- `requests >= 2.25.0`

---

## 🚀 빠른 시작

### 기본 사용법

```
from korector import NaverSpellChecker

checker = NaverSpellChecker()
result = checker.check("안녕 하세요. 저는 한국인 입니다.")

print(result["corrected"])    # 안녕하세요. 저는 한국인입니다.
print(result["error_count"])  # 2
print(result["has_error"])    # True
print(result["time"])         # 0.143
```

### 반환값 예시

```
{
    "success": True,
    "original": "안녕 하세요. 저는 한국인 입니다.",
    "corrected": "안녕하세요. 저는 한국인입니다.",
    "html": "<em class='green_text'>안녕하세요.</em> 저는 <em class='green_text'>한국인입니다.</em>",
    "origin_html": "<span class='result_underline'>안녕 하세요.</span> 저는 <span class='result_underline'>한국인 입니다.</span>",
    "error_count": 2,
    "has_error": True,
    "time": 0.143,
    "raw_response": {...}
}
```

---

## 📖 사용 예제

### 1. 긴 텍스트 처리

```
from korector import NaverSpellChecker

# 진행 상황 콜백
def progress(current, total, result):
    print(f"[{current}/{total}] {result['time']:.3f}s - 변경: {result['has_error']}")

checker = NaverSpellChecker()
long_text = "..." * 1000  # 매우 긴 텍스트

result = checker.check_long_text(
    long_text,
    chunk_size=400,      # 400자씩 분할
    delay=0.5,           # 요청 간 0.5초 대기
    callback=progress    # 진행 상황 출력
)

print(f"총 처리 시간: {result['time']:.2f}초")
print(f"발견된 오류: {result['total_errors']}개")
print(f"교정된 텍스트: {result['corrected']}")
```

**반환값:**

```
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
    "time": 4.52
}
```

### 2. 파일 처리

```
from korector import NaverSpellChecker

checker = NaverSpellChecker()

# 파일 읽기
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 맞춤법 검사
result = checker.check_long_text(text)

# 결과 저장
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(result['corrected'])

print(f"처리 완료! 시간: {result['time']:.2f}초, 오류: {result['total_errors']}개")
```

### 3. 여러 문장 처리

```
from korector import NaverSpellChecker

sentences = [
    "안녕 하세요",
    "저는 한국인 입니다",
    "이문장은 맞춤법이 틀렸어요"
]

checker = NaverSpellChecker()

for sentence in sentences:
    result = checker.check(sentence)
    if result['has_error']:
        print(f"원본: {result['original']}")
        print(f"교정: {result['corrected']}")
        print(f"시간: {result['time']:.3f}초\n")
```

### 4. API 상태 확인

```
from korector import NaverSpellChecker

checker = NaverSpellChecker()
health = checker.health_check()

print(health)
```

**출력:**

```
{
    "status": "ok",
    "passport_key_hash": "a3f2c1d5e6b7...",
    "test_result": {
        "text": "안녕 하세요",
        "corrected": "안녕하세요",
        "error_count": 1,
        "has_error": true,
        "time": 0.152
    }
}
```

---

## 💻 CLI 사용법

### 기본 사용

```
# 단일 문장 검사
$ korector "안녕 하세요"
Time: 0.143s
Errors: 1
Changed: Yes

============================================================
Result:
============================================================
안녕하세요
```

### 파일 처리

```
# 파일 입력/출력
$ korector -f input.txt -o output.txt

# 진행 상황 표시
$ korector -f long_text.txt -o corrected.txt --verbose
```

### 상세 출력

```
# HTML 결과까지 모두 출력
$ korector "아빡가가방에드러간다" --verbose

============================================================
Original:
============================================================
아빡가가방에드러간다

============================================================
Corrected:
============================================================
아빠가 가방에 들어간다

============================================================
HTML:
============================================================
<em class='violet_text'>아빠가 가방에 들어간다</em>

Error type legend:
  - result_underline: Spelling error
  - violet_text: Non-standard word
  - green_text: Spacing error
  - blue_text: Statistical correction
```

### 상태 확인

```
$ korector --health-check
{
  "status": "ok",
  "passport_key_hash": "a3f2c1d5e6b7...",
  "test_result": {
    "text": "안녕 하세요",
    "corrected": "안녕하세요",
    "error_count": 1,
    "has_error": true,
    "time": 0.152
  }
}
```

### CLI 옵션

| 옵션 | 설명 |
|------|------|
| `text` | 검사할 문장 (positional argument) |
| `-f, --file` | 입력 파일 경로 |
| `-o, --output` | 교정 결과 저장 경로 |
| `-c, --chunk-size` | 텍스트 분할 크기 (기본: 400) |
| `--health-check` | API 상태 확인 |
| `-v, --verbose` | 상세 출력 (HTML 포함) |
| `--version` | 버전 정보 출력 |

---

## 📊 반환값 상세

### `check()` 메서드 결과

| Key | Type | 설명 |
|-----|------|------|
| `success` | bool | 검사 성공 여부 |
| `original` | str | 원본 텍스트 |
| `corrected` | str | 교정된 텍스트 (순수 텍스트) |
| `html` | str | 오류 하이라이팅된 HTML |
| `origin_html` | str | 오류 밑줄이 그어진 HTML |
| `error_count` | int | 네이버 API 기준 오류 개수 |
| `has_error` | bool | 텍스트 변경 여부 |
| `time` | float | 응답 시간 (초) |
| `raw_response` | dict | 네이버 API 원본 응답 |

### `check_long_text()` 메서드 결과

| Key | Type | 설명 |
|-----|------|------|
| `success` | bool | 전체 검사 성공 여부 |
| `original` | str | 원본 전체 텍스트 |
| `corrected` | str | 교정된 전체 텍스트 |
| `html` | str | 전체 HTML (하이라이팅) |
| `origin_html` | str | 전체 HTML (밑줄) |
| `total_errors` | int | 총 오류 개수 |
| `has_error` | bool | 텍스트 변경 여부 |
| `chunks_with_errors` | int | 오류가 있는 청크 수 |
| `total_chunks` | int | 전체 청크 수 |
| `failed_chunks` | int | 실패한 청크 수 |
| `time` | float | 전체 처리 시간 (초) |

### HTML 오류 타입

오류 유형은 HTML 클래스로 구분됩니다:

| 클래스 | 의미 |
|--------|------|
| `result_underline` | **맞춤법 오류** |
| `violet_text` | **표준어 의심** |
| `green_text` | **띄어쓰기 오류** |
| `blue_text` | **통계적 교정** |

---

## 🔒 보안 기능

Korector는 다음과 같은 보안 기능을 제공합니다:

- **입력 검증 및 Sanitization** - XSS/JavaScript Injection 방어
- **HMAC 서명** - 요청 무결성 검증
- **passportKey 해시 저장** - 민감 정보 노출 방지
- **입력 길이 제한** - 최대 10,000자
- **안전한 리소스 정리** - 메모리에서 민감 정보 제거

---

## ⚡ 최적화 기능

- **LRU 캐싱** - 정규식 패턴 캐싱으로 성능 향상
- **gzip 압축** - 긴 텍스트 네트워크 전송 최적화
- **멀티스레드 안전** - threading.Lock으로 동시성 보장
- **효율적인 청크 처리** - 긴 텍스트 자동 분할

---

## 📝 주의사항

- 이 라이브러리는 **네이버 한글 맞춤법 검사기**를 기반으로 동작합니다
- 검사 결과 및 데이터에 대한 저작권과 책임은 **네이버 주식회사**에 있습니다
- 상업적 사용이나 대량 호출 시에는 트래픽 및 정책을 반드시 검토해야 합니다
- 네이버 측 정책/응답 포맷 변경 시 라이브러리가 동작하지 않을 수 있습니다
- API 사용량이 많을 경우 일시적으로 차단될 수 있습니다

---

## 📜 라이선스

Apache License 2.0

Copyright (c) 2025 movemin03

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

## 🙏 크레딧

- 네이버 맞춤법 검사기 API
---

## 📞 문의

- GitHub Issues: https://github.com/movemin03/korector/issues

[1](https://img.shields.io/badge/python-3.7+-blue.svg)
[2](https://www.python.org/downloads/)
[3](https://img.shields.io/badge/license-MIT-green.svg)
