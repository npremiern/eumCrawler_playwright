# 빌드 가이드 (Build Instructions)

## 로컬 빌드 (Local Build)

### 현재 플랫폼용 실행 파일 빌드

```bash
python build.py
```

실행 파일 위치:
- Windows: `dist/crawler.exe`
- Mac: `dist/crawler`
- Linux: `dist/crawler`

### 수동 빌드

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. Playwright 브라우저 설치
python -m playwright install chromium

# 3. PyInstaller로 빌드
python -m PyInstaller crawler.spec

# 4. 결과 확인
ls dist/
```

---

## GitHub Actions를 통한 크로스 플랫폼 빌드

### 자동 빌드 설정

프로젝트를 GitHub에 푸시하면 자동으로 Windows, macOS, Linux용 실행 파일이 빌드됩니다.

### 수동 빌드 트리거

1. GitHub 저장소로 이동
2. **Actions** 탭 클릭
3. **Build Executables** workflow 선택
4. **Run workflow** 버튼 클릭
5. 빌드 완료 후 **Artifacts**에서 다운로드

### 빌드된 파일 다운로드

빌드 완료 후 다음 파일들을 다운로드할 수 있습니다:
- `crawler-windows` - Windows EXE
- `crawler-macos` - macOS 실행 파일
- `crawler-linux` - Linux 실행 파일
- `release-packages` - 문서 포함 전체 패키지

---

## Windows에서만 Windows EXE 빌드하기

### 방법 1: 로컬 Windows PC

Windows PC에서:
```cmd
python build.py
```

### 방법 2: Windows VM 사용

Mac/Linux에서 Windows VM을 실행하고 그 안에서 빌드합니다.

### 방법 3: GitHub Actions (권장)

GitHub에 코드를 푸시하면 자동으로 Windows에서 빌드됩니다.

---

## 빌드 문제 해결

### PyInstaller가 없다는 오류
```bash
pip install pyinstaller
```

### Playwright 브라우저가 없다는 오류
```bash
python -m playwright install chromium
```

### 실행 파일이 크다
정상입니다. Playwright 브라우저가 포함되어 있습니다:
- Windows EXE: 약 50-80MB
- 브라우저 포함 시: 약 250-300MB

### Mac에서 "앱이 손상되었습니다" 오류
```bash
xattr -cr dist/crawler
```

---

## GitHub 저장소 초기 설정

### 1. Git 저장소 초기화

```bash
git init
git add .
git commit -m "Initial commit"
```

### 2. GitHub 저장소 생성

1. https://github.com/new 방문
2. 저장소 이름 입력 (예: eumcrawl)
3. Create repository 클릭

### 3. 원격 저장소 연결

```bash
git remote add origin https://github.com/YOUR_USERNAME/eumcrawl.git
git branch -M main
git push -u origin main
```

### 4. 자동 빌드 확인

GitHub Actions 탭에서 빌드 진행 상황을 확인할 수 있습니다.

---

## 릴리스 만들기

### GitHub Release 생성

1. GitHub 저장소의 **Releases** 클릭
2. **Draft a new release** 클릭
3. 태그 버전 입력 (예: v1.0.0)
4. Release 제목과 설명 작성
5. Actions에서 빌드된 파일들을 첨부
6. **Publish release** 클릭

---

## 배포 체크리스트

- [ ] 로컬에서 테스트 완료
- [ ] requirements.txt 최신 상태 확인
- [ ] README.md 업데이트
- [ ] 버전 번호 업데이트 (crawler.py)
- [ ] Git에 커밋 및 푸시
- [ ] GitHub Actions 빌드 성공 확인
- [ ] 빌드된 실행 파일 다운로드 및 테스트
- [ ] GitHub Release 생성
- [ ] 사용자에게 배포

---

## 추가 정보

### 빌드 시간
- GitHub Actions: 각 플랫폼당 약 5-10분
- 로컬 빌드: 약 2-5분

### 파일 크기
- Windows EXE: 50-80MB (압축 시 약 30-40MB)
- macOS/Linux: 40-60MB (압축 시 약 20-30MB)

### 의존성
프로젝트는 다음 라이브러리들을 포함합니다:
- Playwright (브라우저 자동화)
- openpyxl (Excel 처리)
- Click (CLI)
- Rich (터미널 출력)
- Pillow (이미지 처리)
