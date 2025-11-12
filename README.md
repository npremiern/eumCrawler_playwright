# 부동산 정보 자동 크롤링 CLI 프로그램

Excel 파일에서 주소를 읽어 국토교통부 부동산공시가격 알리미 사이트(eum.go.kr)에서 부동산 정보를 자동으로 크롤링하여 Excel 파일에 기록하는 CLI 프로그램입니다.

## 주요 기능

- 📊 Excel 파일 읽기/쓰기 (Office 365 형식)
- 🌐 Playwright를 이용한 웹 크롤링
- 🖼️ 이미지 다운로드 및 Excel 삽입
- 🔄 배치 처리 (여러 주소 자동 반복)
- 📦 Windows EXE 실행 파일로 배포

## 기술 스택

- **언어**: Python 3.11
- **크롤링**: Playwright
- **Excel 처리**: openpyxl
- **CLI**: click
- **로깅/출력**: rich
- **EXE 빌드**: PyInstaller

## 설치 방법

### 개발 환경 설정

```bash
# Python 3.11 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

## 사용 방법

### Excel 파일 구조

Excel 파일은 다음과 같은 구조여야 합니다:

| 열 | 내용 | 입력/출력 |
|---|---|---|
| A | (임의) | - |
| B | 검색할 주소 | 입력 |
| C | 주소 (present_addr) | 출력 |
| D | 분류 (present_class) | 출력 |
| E | 면적 (present_area) | 출력 |
| F | 지가 (jiga) | 출력 |
| G | 표시1 (present_mark1) | 출력 |
| H | 표시2 (present_mark2) | 출력 |
| I | 표시3 (present_mark3) | 출력 |
| J | 이미지 | 출력 |

### CLI 명령어

```bash
# 기본 실행
python crawler.py --file data.xlsx

# 3행부터 시작
python crawler.py --file data.xlsx --start-row 3

# 브라우저 표시 (헤드리스 모드 비활성화)
python crawler.py --file data.xlsx --no-headless

# 상세 로그 출력
python crawler.py --file data.xlsx --verbose

# 대기 시간 조정 (5초)
python crawler.py --file data.xlsx --wait 5
```

### 옵션

| 옵션 | 설명 | 기본값 | 필수 |
|---|---|---|---|
| `--file`, `-f` | Excel 파일 경로 | - | ✓ |
| `--start-row`, `-s` | 시작 행 번호 | 2 | ✗ |
| `--headless/--no-headless` | 헤드리스 모드 | True | ✗ |
| `--wait`, `-w` | 페이지 대기 시간(초) | 3 | ✗ |
| `--verbose`, `-v` | 상세 로그 출력 | False | ✗ |

## EXE 빌드

### 방법 1: 로컬 빌드 (현재 플랫폼)

```bash
# 빌드 스크립트 실행
python build.py
```

빌드가 완료되면:
- Windows: `dist/crawler.exe`
- Mac: `dist/crawler`
- Linux: `dist/crawler`

### 방법 2: GitHub Actions (크로스 플랫폼)

**Windows, macOS, Linux용 실행 파일을 자동으로 빌드합니다.**

1. GitHub에 저장소 생성 및 푸시:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/eumcrawl.git
git push -u origin main
```

2. GitHub Actions가 자동으로 빌드 시작
3. **Actions** 탭에서 빌드 완료 후 **Artifacts** 다운로드

자세한 내용은 [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) 참조

### EXE 사용 방법

```bash
# 기본 실행
crawler.exe --file data.xlsx

# 3행부터 시작, 브라우저 표시
crawler.exe --file data.xlsx --start-row 3 --no-headless

# 상세 로그 출력
crawler.exe --file data.xlsx --verbose
```

## 프로젝트 구조

```
eumcrawl/
├── crawler.py          # 메인 CLI 프로그램
├── scraper.py          # 크롤링 로직
├── excel_handler.py    # Excel 처리 로직
├── config.py           # 설정값
├── requirements.txt    # 의존성
├── crawler.spec        # PyInstaller 설정
├── build.py            # 빌드 스크립트
├── README.md           # 개발 문서
├── README.txt          # 사용자 매뉴얼
└── temp_images/        # 임시 이미지 폴더 (자동 생성)
```

## 개발

### 코드 구조

- **crawler.py**: CLI 인터페이스와 메인 로직
- **scraper.py**: Playwright를 사용한 웹 크롤링
- **excel_handler.py**: openpyxl을 사용한 Excel 파일 처리
- **config.py**: 설정값 및 상수 정의

### 크롤링 프로세스

1. Excel 파일에서 주소 읽기 (B열)
2. eum.go.kr에 접속하여 주소 검색
3. 검색 결과에서 데이터 추출
4. 이미지 다운로드
5. Excel 파일에 데이터 및 이미지 저장
6. 다음 행으로 이동하여 반복

### 에러 핸들링

- Excel 파일 없음: 에러 메시지 출력 후 종료
- 네트워크 오류: 자동 재시도 (최대 3회)
- 검색 결과 없음: 로그 기록 후 다음 행으로 이동
- 이미지 다운로드 실패: 로그 기록 후 이미지 없이 진행

## 성능

- 주소당 평균 처리 시간: 5-10초
- 100개 주소 처리 시간: 약 10-15분
- 네트워크 오류 시 자동 재시도
- 중간 저장으로 데이터 유실 방지

## 시스템 요구사항

- **OS**: Windows 10/11 (64-bit) / macOS / Linux
- **Python**: 3.11+
- **메모리**: 최소 4GB RAM
- **디스크**: 최소 500MB 여유 공간
- **기타**: 인터넷 연결 필요

## 제약사항

- Office 365 Excel 형식만 지원 (.xlsx)
- Chromium 브라우저 필요 (약 200MB)
- 동적 콘텐츠 로딩 시간 필요
- 웹 크롤링 시 사이트 이용 약관 준수 필요

## 라이선스

MIT License

## 문의

이슈 및 문의사항은 GitHub Issues에 등록해주세요.
