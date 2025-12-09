# Korector

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

**Korector**는 네이버 맞춤법 검사기를 이용한 파이썬용 한글 맞춤법/띄어쓰기 검사 라이브러리입니다.

자동 청킹, 병렬 처리, passportKey 자동 관리 등의 기능을 제공합니다.

---

## ✨ 특징

- ✅ **네이버 맞춤법 검사기** 기반 정확한 한글 맞춤법/띄어쓰기 검사
- ✅ **자동 토큰 관리** - passportKey 자동 추출 및 갱신
- ✅ **자동 청킹** - 긴 텍스트를 450자씩 자동 분할 처리
- ✅ **병렬 처리** - 멀티스레드로 빠른 검사 (최대 3개 동시 요청)
- ✅ **응답 시간 측정** - 모든 요청에 대한 정확한 시간 추적
- ✅ **상세한 결과** - HTML 하이라이팅 및 오류 통계 포함
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
    "time": 0.143
}
```

---

## 📖 사용 예제

### 1. 긴 텍스트 자동 처리

```
from korector import NaverSpellChecker

checker = NaverSpellChecker()

# 긴 텍스트는 자동으로 450자씩 나눠서 병렬 처리
long_text = "..." * 1000  # 매우 긴 텍스트

result = checker.check(long_text)  # auto_split=True가 기본값

print(f"총 처리 시간: {result['time']:.2f}초")
print(f"발견된 오류: {result['total_errors']}개")
print(f"처리된 청크: {result['total_chunks']}개")
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
    "total_chunks": 8,
    "failed_chunks": 0,
    "time": 2.15  # 병렬 처리로 시간 단축
}
```

### 2. 파일 처리

```
from korector import NaverSpellChecker

checker = NaverSpellChecker()

# 파일 읽기 (인코딩 자동 처리)
try:
    with open('input.txt', 'r', encoding='utf-8') as f:
        text = f.read()
except UnicodeDecodeError:
    with open('input.txt', 'r', encoding='cp949') as f:
        text = f.read()

# 맞춤법 검사 (자동으로 청킹 및 병렬 처리)
result = checker.check(text)

# 결과 저장
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(result['corrected'])

print(f"처리 완료! 시간: {result['time']:.2f}초")
if 'total_errors' in result:
    print(f"총 오류: {result['total_errors']}개, 청크: {result['total_chunks']}개")
else:
    print(f"오류: {result['error_count']}개")
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
    "test_result": {
        "text": "안녕 하세요",
        "corrected": "안녕하세요",
        "error_count": 1,
        "has_error": True,
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
처리 시간: 0.143초
오류 개수: 1
변경 여부: 있음

============================================================
결과:
============================================================
안녕하세요
```

### 파일 처리

```
# 파일 입력/출력 (자동으로 청킹 및 병렬 처리)
$ korector -f input.txt -o output.txt

총 8개 청크로 분할하여 병렬 처리 시작...
  ✓ 청크 1/8 완료 (0.14초)
  ✓ 청크 2/8 완료 (0.15초)
  ...
처리 시간: 2.15초
전체 오류: 10
처리 청크: 8
변경 여부: 있음

저장 완료: output.txt
```

### 상세 출력

```
# HTML 결과까지 모두 출력
$ korector "아빡가가방에드러간다" --verbose

처리 시간: 0.152초
오류 개수: 1
변경 여부: 있음

============================================================
원본:
============================================================
아빡가가방에드러간다

============================================================
교정:
============================================================
아빠가 가방에 들어간다

============================================================
HTML (오류 표시):
============================================================
<em class='violet_text'>아빠가 가방에 들어간다</em>
```

### 상태 확인

```
$ korector --health-check
{
  "status": "ok",
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
| `--health-check` | API 상태 확인 |
| `-v, --verbose` | 상세 출력 (HTML 포함) |
| `--version` | 버전 정보 출력 |

---

## 📊 반환값 상세

### 짧은 텍스트 (`check()` 단일 요청)

| Key | Type | 설명 |
|-----|------|------|
| `success` | bool | 검사 성공 여부 |
| `original` | str | 원본 텍스트 |
| `corrected` | str | 교정된 텍스트 |
| `html` | str | 오류 하이라이팅된 HTML |
| `origin_html` | str | 오류 밑줄이 그어진 HTML |
| `error_count` | int | 네이버 API 기준 오류 개수 |
| `has_error` | bool | 텍스트 변경 여부 |
| `time` | float | 응답 시간 (초) |

### 긴 텍스트 (자동 청킹 및 병렬 처리)

| Key | Type | 설명 |
|-----|------|------|
| `success` | bool | 전체 검사 성공 여부 |
| `original` | str | 원본 전체 텍스트 |
| `corrected` | str | 교정된 전체 텍스트 |
| `html` | str | 전체 HTML (하이라이팅) |
| `origin_html` | str | 전체 HTML (밑줄) |
| `total_errors` | int | 총 오류 개수 |
| `has_error` | bool | 텍스트 변경 여부 |
| `total_chunks` | int | 처리된 청크 수 |
| `failed_chunks` | int | 실패한 청크 수 |
| `time` | float | 전체 처리 시간 (초) |

### HTML 오류 타입

| 클래스 | 의미 |
|--------|------|
| `result_underline` | **맞춤법 오류** |
| `violet_text` | **표준어 의심** |
| `green_text` | **띄어쓰기 오류** |
| `blue_text` | **통계적 교정** |

---

## ⚡ 성능 최적화

- **자동 청킹** - 450자 기준으로 자동 분할
- **병렬 처리** - ThreadPoolExecutor로 최대 3개 동시 요청
- **순서 보존** - 청크 번호로 원본 순서 유지
- **LRU 캐싱** - 정규식 패턴 캐싱으로 성능 향상
- **자동 재시도** - passportKey 만료 시 자동 갱신

---

## 📝 주의사항

- 이 라이브러리는 **네이버 한글 맞춤법 검사기**를 기반으로 동작합니다
- 검사 결과 및 데이터에 대한 저작권과 책임은 **네이버 주식회사**에 있습니다
- 상업적 사용이나 대량 호출 시에는 트래픽 및 정책을 반드시 검토해야 합니다
- 네이버 측 정책/응답 포맷 변경 시 라이브러리가 동작하지 않을 수 있습니다
- 병렬 처리 시 네이버 서버 부담을 고려하여 최대 3개로 제한되어 있습니다

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
