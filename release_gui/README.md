# 토지이용계획확인원 데이터 가져오기 (EUM Crawler)

부동산 정보를 자동으로 수집하는 크롤러 프로그램입니다.

## 📂 프로젝트 구조

```
eumCrawler_playwright/
├── src/                    # 핵심 실행 파일
│   ├── crawler.py          # CLI 실행 파일
│   ├── crawler_gui.py      # GUI 실행 파일
│   ├── scraper.py          # 웹 스크래핑 로직
│   ├── excel_handler.py    # Excel 파일 처리
│   ├── config.py           # 설정 파일
│   └── console_helper.py   # 콘솔 출력 헬퍼
│
├── build_tools/            # 빌드 관련 파일
│   ├── build.py            # CLI 빌드 스크립트
│   ├── build_gui.py        # GUI 빌드 스크립트
│   ├── build_all_platforms.py  # 멀티 플랫폼 빌드
│   ├── build_release.py    # 릴리스 빌드
│   ├── crawler.spec        # CLI PyInstaller 설정
│   └── crawler_gui.spec    # GUI PyInstaller 설정
│
├── dev_tools/              # 개발/테스트 도구
│   ├── test_excel.py       # Excel 기능 테스트
│   ├── test_image_download.py  # 이미지 다운로드 테스트
│   ├── test_korean_filename.py # 한글 파일명 테스트
│   ├── debug_image_url.py  # 이미지 URL 디버깅
│   ├── debug_selectors.py  # CSS 셀렉터 디버깅
│   └── create_example_data.py  # 예제 데이터 생성
│
├── docs/                   # 문서 파일
│   ├── README.txt          # 사용자 가이드 (텍스트)
│   ├── INSTALL_GUIDE.txt   # 설치 가이드
│   ├── BUILD_INSTRUCTIONS.md   # 빌드 방법
│   ├── CHANGELOG.md        # 변경 이력
│   ├── REFACTORING_SUMMARY.md  # 리팩토링 요약
│   ├── CLAUDE.md           # Claude AI 관련 문서
│   └── 사용설명서.txt       # 한글 사용 설명서
│
├── build/                  # 빌드 임시 파일
├── dist/                   # 빌드 결과물
├── release_gui/            # GUI 릴리스 패키지
├── images/                 # 다운로드된 이미지 저장소
├── build_scripts/          # 추가 빌드 스크립트
│
├── requirements.txt        # Python 의존성
├── .gitignore             # Git 제외 파일 목록
├── example_data.xlsx      # 예제 데이터 파일
├── install_browser.bat    # 브라우저 설치 스크립트
└── install_chromium_from_zip.bat  # Chromium 설치 스크립트
```

## 🚀 빠른 시작

### 1. 요구사항
- Python 3.8 이상
- Playwright 브라우저

### 2. 설치
```bash
# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 3. 실행

**GUI 버전 (권장)**
```bash
python src/crawler_gui.py
```

**CLI 버전**
```bash
python src/crawler.py -f example_data.xlsx
```

## 📖 상세 문서

- **사용 방법**: [docs/사용설명서.txt](docs/사용설명서.txt)
- **설치 가이드**: [docs/INSTALL_GUIDE.txt](docs/INSTALL_GUIDE.txt)
- **빌드 방법**: [docs/BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md)
- **변경 이력**: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## 🛠️ 개발

### 테스트 실행
```bash
# Excel 기능 테스트
python dev_tools/test_excel.py

# 이미지 다운로드 테스트
python dev_tools/test_image_download.py
```

### 빌드
```bash
# GUI 실행파일 빌드
python build_tools/build_gui.py

# CLI 실행파일 빌드
python build_tools/build.py
```

## 📝 라이선스

이 프로젝트는 개인 용도로 제작되었습니다.

## 🔄 최근 업데이트

자세한 변경 사항은 [docs/CHANGELOG.md](docs/CHANGELOG.md)를 참고하세요.
