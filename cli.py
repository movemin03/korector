name: Korector Health Monitor

on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

permissions:
  contents: read
  issues: write

jobs:
  # 🖥️ Windows 테스트 (정확한 헤더 적용)
  windows-test:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.13'
    
    - name: 🧹 Clean & Build (Windows)
      shell: powershell
      run: |
        pip install --upgrade pip build setuptools wheel
        if (Test-Path "dist") { Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue }
        if (Test-Path "build") { Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue }
        Get-ChildItem -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        try { pip uninstall korector -y } catch {}
        python -m build
        pip install .
        pip show korector

    - name: 🔍 Windows Naver Debug (정확한 헤더)
      shell: powershell
      run: |
        python - << 'EOF'
        import requests
        import re
        
        print("🖥️ Windows - 네이버 요청 (로컬 성공 헤더 재현)")
        print("=" * 70)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'Sec-Ch-Ua-Arch': '"x86"',
            'Sec-Ch-Ua-Bitness': '"64"',
            'Sec-Ch-Ua-Full-Version-List': '"Microsoft Edge";v="143.0.3650.66", "Chromium";v="143.0.7499.41", "Not A(Brand";v="24.0.0.0"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Model': '""',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Ch-Ua-Platform-Version': '"19.0.0"',
            'Sec-Ch-Ua-WoW64': '?0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.naver.com/',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # 🔑 로컬 성공 URL 사용
        url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EB%84%A4%EC%9D%B4%EB%B2%84+%EB%A7%9E%EC%B6%A4%EB%B2%95+%EA%B2%80%EC%82%AC%EA%B8%B0&ackey=b3lkpta1'
        resp = session.get(url, timeout=15)
        
        print(f"✅ Status: {resp.status_code}")
        print(f"📏 Length: {len(resp.text):,} bytes")
        
        # passportKey 검색
        patterns = [
            r'passportKey["\']?\s*[:=]\s*["\']([a-f0-9]{40})',
            r'([a-f0-9]{40})\s*["\']?\s*(?:SpellerProxy|checker)',
            r'SpellerProxy[^>]*passportKey["\']?\s*[:=]\s*["\']([a-f0-9]{40})',
        ]
        
        for i, pattern in enumerate(patterns, 1):
            matches = re.findall(pattern, resp.text, re.IGNORECASE)
            if matches:
                print(f"✅ 패턴{i}: {matches[0][:16]}...")
                break
        
        EOF

    - name: 🖥️ Windows korector --health-check
      shell: powershell
      run: |
        Write-Output "🖥️ Windows Platform Test (1.0.6)"
        python -c "from korector import NaverSpellChecker; c=NaverSpellChecker(verbose=True); print('Python:', c.health_check())"
        korector --health-check --verbose
        Write-Output "✅ Windows Test Complete"

  # 🐧 Linux 테스트 (Ubuntu)
  linux-test
