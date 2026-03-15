# 부동산공시가격 크롤러 v2.0 - 제품 요구사항 문서 (PRD)

**문서 번호**: PRD-2026-001
**작성일**: 2026-03-10
**최종 수정**: 2026-03-10
**버전**: 1.0.0
**상태**: 최종 승인 대기

---

## 목차

1. [개요](#개요)
2. [프로젝트 배경](#프로젝트-배경)
3. [제품 비전 및 목표](#제품-비전-및-목표)
4. [기술 스택](#기술-스택)
5. [기능 요구사항 (Functional Requirements)](#기능-요구사항-functional-requirements)
6. [비기능 요구사항 (Non-Functional Requirements)](#비기능-요구사항-non-functional-requirements)
7. [데이터 모델](#데이터-모델)
8. [사용자 인터페이스 요구사항](#사용자-인터페이스-요구사항)
9. [통합 및 API](#통합-및-api)
10. [보안 및 규정 준수](#보안-및-규정-준수)
11. [배포 및 유지보수](#배포-및-유지보수)
12. [범위 제외 (Out of Scope)](#범위-제외-out-of-scope)
13. [마이그레이션 전략](#마이그레이션-전략)
14. [성공 기준](#성공-기준)

---

## 개요

### 제품명
**부동산공시가격 크롤러 v2.0** (eumCrawler v2.0)

### 한 줄 설명
국토교통부 부동산공시가격 알리미(eum.go.kr)에서 대량의 부동산 공시가격 정보를 자동으로 수집하고 관리하는 현대화된 데스크톱 애플리케이션

### 주요 개선사항
- 기존 Python CLI 기반 → Tauri + Svelte 데스크톱 앱으로 전환
- Excel 중심 워크플로우 → SQLite 데이터베이스 기반 워크플로우로 전환
- 실시간 진행률 표시 및 일시정지/재개 기능 추가
- 스마트 캐싱으로 중복 크롤링 제거
- 향상된 UX와 대시보드 추가

---

## 프로젝트 배경

### 현재 상태 (v1.x)
- **기술 스택**: Python + Click + Playwright + openpyxl
- **배포 형태**: CLI 기반 실행 또는 PyInstaller를 통한 단일 EXE
- **데이터 흐름**:
  - Excel 파일에서 주소 읽기 (B 컬럼)
  - eum.go.kr 검색 및 크롤링
  - 결과를 Excel에 다시 쓰기 (C~J 컬럼)
  - 이미지 다운로드 및 Excel에 삽입
- **주요 문제점**:
  - CLI 인터페이스로 인한 사용자 경험 제한
  - 중복 크롤링으로 인한 시간 낭비
  - 진행 상황을 보기 어려움
  - Excel 파일 기반의 데이터 관리의 한계
  - 배치 작업 관리 기능 부재

### 마이그레이션 목표
1. 현대화된 GUI 제공으로 사용성 향상
2. 데이터베이스를 통한 효율적인 데이터 관리
3. 스마트 캐싱으로 성능 개선
4. 배치 작업 관리 및 스케줄링 기능
5. 향상된 검색 및 필터링
6. 개선된 배포 및 유지보수성

---

## 제품 비전 및 목표

### 제품 비전
사용자가 복잡한 명령어 없이도 직관적인 인터페이스를 통해 부동산 공시가격 정보를 효율적으로 수집, 관리, 분석할 수 있는 통합 플랫폼을 제공한다.

### 비즈니스 목표
1. **사용성 향상**: 기술적 지식이 없는 사용자도 쉽게 사용 가능
2. **효율성 증대**: 캐싱으로 크롤링 시간 30% 이상 단축
3. **신뢰성 강화**: SQLite 기반으로 데이터 무결성 보장
4. **확장성 확보**: 향후 기능 추가가 용이한 아키텍처
5. **유지보수성 개선**: 현대 기술 스택으로 장기 지원 가능

### 성공 지표
- 사용자 작업 시간 50% 감소
- 데이터 손실률 0%
- 캐시 히트율 40% 이상 (반복 크롤링 시)
- UI 응답성 500ms 이내 (모든 작업)
- 설치 및 실행 성공률 99%

---

## 기술 스택

### 프론트엔드
- **프레임워크**: Svelte 5 (with runes)
- **스타일링**: Tailwind CSS
- **상태 관리**: Svelte stores (runes 기반)
- **UI 컴포넌트**: SvelteUI 또는 Skeleton UI
- **패키지 매니저**: Bun

### 백엔드/데스크톱
- **프레임워크**: Tauri v2 (Rust)
- **런타임**: Node.js / Bun (JavaScript 런타임)
- **크롤러**: Playwright (Bun sidecar로 실행)
- **데이터베이스**: SQLite 3 (WAL 모드)
- **로깅**: structured logging (JSON 형식)

### 개발 도구
- **빌드**: Tauri CLI
- **테스트**: Vitest (프론트엔드), pytest (백엔드)
- **정적 분석**: ESLint, Prettier
- **타입 체크**: TypeScript

### 배포
- **Windows**: MSI 설치 프로그램 또는 NSIS 기반 exe
- **패키징**: Tauri 번들러

### 호환 운영체제
- **주요**: Windows 10/11 (64-bit)
- **보조**: macOS 11+ (Apple Silicon 지원)
- **기타**: Linux (GTK 기반, 선택사항)

---

## 기능 요구사항 (Functional Requirements)

### FR-01: 주소 관리

#### FR-01.1: Excel 파일에서 주소 가져오기
- **설명**: Excel 파일의 B 컬럼에서 주소 목록을 읽어 앱으로 가져오기
- **상세 요구사항**:
  - 지원 형식: .xlsx (Office 365 형식)
  - B 컬럼에서 주소 추출 (행 2부터 시작, 헤더는 행 1)
  - A 컬럼의 ID가 있으면 함께 가져오기
  - 중복 주소 감지 및 경고
  - 가져오기 진행률 표시
  - 가져오기 완료 후 요약 통계 표시 (총 개수, 중복, 새로 추가된 개수)
- **예외 처리**:
  - 파일 열기 실패 시 명확한 오류 메시지
  - 빈 행 만나면 그 이후는 무시
  - 유효하지 않은 Excel 파일 형식 감지

#### FR-01.2: 수동 주소 입력
- **설명**: 사용자가 앱 내에서 직접 주소를 입력
- **상세 요구사항**:
  - 단일 주소 입력 필드
  - 한국 주소 검증 (기본: 길이 확인, 선택사항: 실제 주소 DB 검증)
  - 태그 추가 기능 (선택사항)
  - "추가" 버튼 클릭 시 DB에 저장
  - 성공 메시지 표시

#### FR-01.3: 주소 목록 조회 및 CRUD
- **설명**: 입력된 모든 주소를 목록으로 보여주고 편집/삭제 가능
- **상세 요구사항**:
  - 테이블 형식으로 주소 목록 표시
  - 컬럼: ID, 주소, 그룹/태그, 입력일, 상태 (미크롤링/크롤링됨/실패)
  - 페이지네이션 (페이지당 50개)
  - 주소 클릭 시 상세 정보 모달
  - 수정: 주소 및 태그 편집 가능
  - 삭제: 단일/다중 선택 삭제
  - 삭제 전 확인 대화창
  - 삭제 시 관련 크롤링 결과도 함께 삭제 여부 사용자 선택

#### FR-01.4: 주소 그룹/태그
- **설명**: 주소를 분류하여 조직화
- **상세 요구사항**:
  - 그룹(폴더 개념) 생성/수정/삭제
  - 각 주소에 태그 최대 5개까지 지정 가능
  - 그룹별로 주소 필터링
  - 태그별로 주소 필터링
  - 그룹 삭제 시 주소는 유지 (그룹만 제거)

### FR-02: 크롤링 엔진

#### FR-02.1: 2단계 크롤링 프로세스
- **설명**: 기존 v1.x와 동일한 2단계 프로세스 유지
  1. **검증 단계**: 주소가 eum.go.kr에서 유효한지 확인
  2. **스크래핑 단계**: 유효한 경우 상세 정보 추출
- **상세 요구사항**:
  - 단계별 진행률 표시
  - 각 단계에서 실패하면 다음 단계 스킵
  - 재시도 로직 (최대 3회)
  - 재시도 간격: 5초 (기본값, 설정에서 변경 가능)

#### FR-02.2: 실시간 진행률 표시
- **설명**: 크롤링 진행 상황을 실시간으로 사용자에게 표시
- **상세 요구사항**:
  - 진행률 바 (퍼센트 표시)
  - 현재 처리 중인 주소 표시
  - 처리 완료/실패/스킵 건수 카운터
  - 예상 완료 시간 표시 (현재까지의 평균 속도 기반)
  - 처리 속도 (주소/분) 표시
  - 상태: 실행 중 / 일시정지됨 / 완료 / 오류

#### FR-02.3: 일시정지/재개/중단 기능
- **설명**: 사용자가 크롤링 작업을 제어
- **상세 요구사항**:
  - **일시정지**: 현재 작업 완료 후 멈춤 (상태 저장)
  - **재개**: 중단된 지점에서부터 다시 시작
  - **중단**: 즉시 중단 (현재 진행 중인 항목은 완료할 때까지 기다림)
  - 각 버튼의 활성화 조건 명확 (실행 중일 때만 일시정지, 일시정지 중일 때만 재개 등)
  - 작업 중단 시 "작업을 중단하시겠습니까?" 확인

#### FR-02.4: 크롤링 설정
- **설명**: 크롤링 동작을 제어하는 설정들
- **상세 요구사항**:
  - **스케일**: 지도 스케일 선택 (1/600, 1/1200, 1/2400, 1/4800, 1/12000)
    - 기본값: 1/2400
    - 설명: 토지이용계획확인원 PDF 다운로드 시 사용
  - **대기 시간**: 각 요청 간 대기 시간 (초)
    - 범위: 1~10초
    - 기본값: 3초
  - **헤드리스 모드**: 브라우저 창 표시 여부
    - ON (기본): 백그라운드 실행
    - OFF: 브라우저 창 표시 (디버깅용)
  - **강제 새로고침**: 캐시를 무시하고 항상 크롤링
  - 설정 변경 시 실시간 적용

#### FR-02.5: 재시도 로직
- **설명**: 네트워크 오류나 타임아웃 시 자동 재시도
- **상세 요구사항**:
  - 최대 재시도 횟수: 3회
  - 재시도 대기: 5초 (증가식 백오프는 선택사항)
  - 재시도 실패 시 오류 메시지 기록
  - 오류 유형별 처리:
    - 네트워크 에러: 자동 재시도
    - 타임아웃: 자동 재시도
    - 페이지 로드 실패: 자동 재시도
    - "검색 결과 없음": 재시도 안 함 (스킵)
    - 데이터 추출 실패: 재시도 안 함 (부분 데이터만 저장)

#### FR-02.6: 백그라운드 처리
- **설명**: 크롤링 작업이 UI를 차단하지 않음
- **상세 요구사항**:
  - Tauri 커맨드를 async로 실행
  - UI는 항상 반응성 유지 (500ms 이내 응답)
  - 크롤링 중에도 다른 작업 가능 (검색, 필터링, 설정 변경 등)
  - 작업 진행 상황은 웹소켓 또는 이벤트 기반으로 실시간 업데이트

### FR-03: 데이터 캐시 및 재사용

#### FR-03.1: 캐시 조회
- **설명**: 크롤링 전에 데이터베이스에서 기존 데이터 확인
- **상세 요구사항**:
  - 주소로 DB에서 기존 결과 검색
  - 캐시 유효성 확인 (expires_at 필드 비교)
  - 캐시 유효하면: "캐시된 데이터 사용" 표시
  - 캐시 무효하면: 새로 크롤링

#### FR-03.2: 캐시 저장 및 갱신
- **설명**: 크롤링 결과를 캐시로 저장
- **상세 요구사항**:
  - crawl_results 테이블에 결과 저장
  - expires_at 필드에 만료 일시 자동 계산
    - 만료 기간 = 설정의 캐시 만료 기간
  - 결과 상태 저장 (success, failed, partial)

#### FR-03.3: 캐시 만료 설정
- **설명**: 캐시 유효 기간 설정
- **상세 요구사항**:
  - 선택 옵션: 7일, 14일, 30일, 60일, 90일, 180일, 365일, 무한
  - 기본값: 30일
  - 설정 변경 시 기존 캐시에는 영향 없음 (새로운 크롤링부터 적용)
  - 설정 화면에 "캐시 통계" 표시 (전체 캐시 수, 유효한 캐시 수, 만료된 캐시 수)

#### FR-03.4: 강제 새로고침 옵션
- **설명**: 사용자가 명시적으로 캐시를 무시하고 다시 크롤링
- **상세 요구사항**:
  - 각 작업 상세보기에 "강제 새로고침" 버튼
  - 결과 목록에서 다중 선택 후 "선택 항목 다시 크롤링" 옵션
  - 강제 새로고침 실행 시 기존 결과는 새로 크롤링한 결과로 덮어쓰기

#### FR-03.5: 캐시 관리
- **설명**: 캐시 데이터의 정리 및 통계
- **상세 요구사항**:
  - **캐시 정리**: 만료된 캐시 자동 삭제 (스케줄: 주 1회 또는 앱 시작 시)
  - **수동 정리**: 사용자가 만료된 캐시 또는 전체 캐시 수동 삭제 가능
  - **캐시 통계**: 캐시 크기, 개수, 히트율 등 표시
  - 캐시 상태 시각화:
    - 녹색: 유효한 캐시 (만료까지 X일)
    - 주황색: 만료 예정 (만료까지 1일 이내)
    - 회색: 만료된 캐시

### FR-04: 결과 관리

#### FR-04.1: 결과 목록 조회
- **설명**: 크롤링된 모든 결과를 테이블로 표시
- **상세 요구사항**:
  - 컬럼: ID, 주소, PNU, 공시지가, 면적, 표시1/2/3, 크롤링 일시, 상태, 캐시 여부
  - 기본 정렬: 크롤링 일시 (최신순)
  - 페이지네이션: 페이지당 50개
  - 행 클릭 시 상세보기 모달 열기
  - 다중 선택 가능 (체크박스)

#### FR-04.2: 상세보기
- **설명**: 개별 결과의 모든 정보를 표시
- **상세 요구사항**:
  - **기본 정보**: 주소, PNU, 공시가격년도, 크롤링 일시
  - **추출된 데이터**: 공시지가, 면적, 표시1/2/3 등 모든 필드
  - **이미지**: 다운로드된 이미지 미리보기
  - **PDF**: 토지이용계획확인원 PDF 링크 (클릭 시 열기)
  - **메타데이터**: 캐시 여부, 캐시 만료일, 생성일, 마지막 수정일
  - **액션**: 강제 새로고침, 편집, 삭제, 내보내기

#### FR-04.3: 검색 기능
- **설명**: 특정 결과를 빠르게 찾기
- **상세 요구사항**:
  - 검색 필드:
    - 주소 (부분 검색 가능)
    - PNU (정확 검색)
    - ID (정확 검색)
  - 실시간 검색 (입력하면서 즉시 필터링)
  - 검색 결과 개수 표시

#### FR-04.4: 필터링
- **설명**: 조건에 따라 결과 필터링
- **상세 요구사항**:
  - **날짜 범위**: 크롤링 날짜 (From ~ To)
  - **상태**: 성공 / 실패 / 부분 데이터
  - **캐시 상태**: 캐시됨 / 신규 크롤링
  - **지역**: 시/도 선택 (주소에서 자동 추출)
  - 복합 필터링 가능 (조건 AND 조합)
  - 필터 초기화 버튼

#### FR-04.5: 정렬
- **설명**: 결과를 다양한 기준으로 정렬
- **상세 요구사항**:
  - 정렬 가능 컬럼: 주소, 공시지가, 면적, 크롤링 일시, 상태
  - 오름차순 / 내림차순 선택 가능
  - 클릭 시 정렬 적용

#### FR-04.6: 벌크 작업
- **설명**: 여러 결과에 대해 한 번에 작업
- **상세 요구사항**:
  - **다중 선택**: 체크박스로 여러 항목 선택
  - **전체 선택**: 페이지 전체 또는 필터된 모든 항목 선택
  - **삭제**: 선택된 항목 일괄 삭제
  - **다시 크롤링**: 선택된 항목 강제 새로고침
  - **내보내기**: 선택된 항목만 내보내기
  - 각 작업 실행 전 확인 대화창

### FR-05: 이미지 및 PDF 관리

#### FR-05.1: 이미지 다운로드
- **설명**: 부동산 공시가격 알리미에서 표시된 이미지 다운로드
- **상세 요구사항**:
  - CSS 선택자: `#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img`
  - 다운로드 위치: 설정에서 지정한 디렉토리
  - 파일명: `{PNU}_{YYYYMMDD}.jpg`
  - 이미지 포맷: JPG (원본 유지)
  - 다운로드 실패 시 경고 로그만 기록 (프로세스 계속 진행)

#### FR-05.2: 이미지 미리보기
- **설명**: 앱 내에서 다운로드된 이미지 표시
- **상세 요구사항**:
  - 결과 상세보기에서 이미지 미리보기
  - 이미지 클릭 시 전체 화면으로 보기
  - 이미지 없으면 "이미지 없음" 표시

#### FR-05.3: PDF 다운로드 (토지이용계획확인원)
- **설명**: 토지이용계획확인원 PDF 다운로드
- **상세 요구사항**:
  - PDF 링크 자동 생성 (지도 스케일 기반)
  - 다운로드 위치: 설정에서 지정한 디렉토리
  - 파일명: `{PNU}_토지이용계획_{YYYYMMDD}.pdf`
  - 다운로드 실패 시 경고 로그만 기록
  - PDF 링크를 앱 내에서 열 수 있도록 제공

#### FR-05.4: 파일 관리
- **설명**: 다운로드된 이미지 및 PDF의 저장소 관리
- **상세 요구사항**:
  - 저장 경로 설정 가능 (기본: %APPDATA%\eumcrawler\media)
  - 설정 변경 시 기존 파일 이동 여부 사용자 선택
  - 저장소 사용량 표시 (설정 화면)
  - 오래된 파일 삭제 옵션 (선택사항: 90일 이상)

### FR-06: 내보내기

#### FR-06.1: Excel 내보내기
- **설명**: 크롤링 결과를 Excel 파일로 내보내기
- **상세 요구사항**:
  - 출력 형식: .xlsx (Office 365)
  - 기본 컬럼: ID, 주소, PNU, 공시지가, 면적, 표시1/2/3, 크롤링 일시, 상태
  - 선택적 컬럼:
    - 이미지 (이미지 파일 경로)
    - PDF (PDF 파일 경로)
    - 캐시 여부
    - 캐시 만료일
  - 컬럼 선택: 사용자가 내보낼 컬럼 선택 가능
  - 이미지 임베딩 옵션:
    - OFF (기본): 파일 경로만 저장
    - ON: Excel에 이미지 삽입 (이미지 파일 각각 300px 폭)
      - 주의: 이미지가 많으면 파일 크기 커짐
  - 정렬: 현재 테이블의 정렬 상태 유지
  - 필터: 현재 필터 상태 무시하고 선택된 항목만 내보내기
  - 진행률 표시
  - 저장 위치: 사용자가 선택

#### FR-06.2: CSV 내보내기
- **설명**: 크롤링 결과를 CSV 파일로 내보내기
- **상세 요구사항**:
  - 문자 인코딩: UTF-8 with BOM (Excel에서 올바르게 열기 위함)
  - 구분자: 쉼표 (,)
  - 텍스트 정렬: 큰따옴표 (")
  - 헤더 행: 포함
  - 특수 문자 처리: 이스케이프 처리
  - 선택적 컬럼: Excel과 동일

### FR-07: 배치 작업 관리

#### FR-07.1: 작업 생성
- **설명**: 새로운 크롤링 작업 생성
- **상세 요구사항**:
  - **작업명**: 사용자가 지정 (예: "서울시 강남구 크롤링", "2026년 3월 일괄")
  - **작업 소스**:
    - 기존 주소 목록에서 선택 (전체 또는 특정 그룹/태그)
    - Excel 파일에서 새로 가져오기
    - 수동으로 주소 목록 붙여넣기
  - **우선순위**: 높음 / 보통 / 낮음 (기본: 보통)
  - **생성 후**: 즉시 실행 또는 큐에 추가
  - 작업 ID 자동 생성 및 표시

#### FR-07.2: 작업 대기열 (Job Queue)
- **설명**: 여러 작업을 순서대로 처리
- **상세 요구사항**:
  - 동시 실행: 최대 1개 (순차 실행)
  - 우선순위 처리: 높음 > 보통 > 낮음
  - 동일 우선순위: 생성 순서
  - 대기 중인 작업 목록 표시
  - 각 작업의 예상 시작 시간 표시 (큐의 위치 기반)

#### FR-07.3: 작업 상태 추적
- **설명**: 작업의 진행 상황 및 상태 추적
- **상세 요구사항**:
  - 상태: 대기 중 / 실행 중 / 일시정지 / 완료 / 실패
  - 진행률: (완료 + 실패) / 전체 × 100%
  - 처리 현황: 완료 수 / 전체 수, 실패 수, 스킵 수
  - 시간 정보: 생성일, 시작일, 완료일, 소요 시간
  - 실패 상세: 실패한 항목 목록 (클릭하여 상세정보 보기)

#### FR-07.4: 작업 제어
- **설명**: 작업 실행, 일시정지, 재개, 취소
- **상세 요구사항**:
  - **즉시 실행**: 대기 중인 작업을 큐에 상관없이 즉시 실행 (우선순위 높음으로 변경)
  - **일시정지**: 현재 작업을 일시정지
  - **재개**: 일시정지된 작업 계속 처리
  - **취소**: 작업 취소 (완료된 작업은 취소 불가)
    - 대기 중: 즉시 취소
    - 실행 중: 현재 항목 처리 완료 후 취소
  - 각 작업 상태별로 가능한 작업만 버튼 활성화

#### FR-07.5: 작업 이력
- **설명**: 실행된 작업의 이력 관리
- **상세 요구사항**:
  - 완료된 작업 목록 표시 (테이블)
  - 컬럼: 작업명, 완료일, 전체 수, 성공 수, 실패 수, 소요 시간, 상태
  - 정렬 가능: 완료일 (기본 최신순), 작업명, 상태 등
  - 이력 검색: 작업명으로 검색
  - 이력 상세보기: 각 작업의 처리 항목 목록
  - 이력 삭제: 완료된 이력 삭제 (관련 결과는 유지)

### FR-08: 설정

#### FR-08.1: 크롤러 설정
- **설명**: 크롤링 동작을 제어하는 설정
- **상세 요구사항**:
  - **캐시 만료 기간**: 7/14/30/60/90/180/365일, 무한
    - 기본값: 30일
  - **기본 지도 스케일**: 1/600 ~ 1/12000 (기본: 1/2400)
  - **요청 간 대기 시간**: 1~10초 (기본: 3초)
  - **헤드리스 모드**: ON/OFF (기본: ON)
  - **최대 재시도 횟수**: 1~5 (기본: 3)
  - **페이지 로드 타임아웃**: 10~60초 (기본: 30초)

#### FR-08.2: 파일 저장소 설정
- **설명**: 데이터 및 파일 저장 위치 설정
- **상세 요구사항**:
  - **이미지 저장 경로**: 기본값 %APPDATA%\eumcrawler\images
  - **PDF 저장 경로**: 기본값 %APPDATA%\eumcrawler\pdfs
  - **데이터베이스 저장 경로**: 기본값 %APPDATA%\eumcrawler\data
  - **경로 선택**: 폴더 브라우저 다이얼로그
  - **경로 유효성 확인**: 경로가 존재하는지, 쓰기 권한이 있는지 확인
  - 경로 변경 시 기존 파일 이동 여부 사용자 선택

#### FR-08.3: 자동 저장 및 백업
- **설명**: 데이터 자동 저장 및 백업 설정
- **상세 요구사항**:
  - **자동 저장**: 매 작업마다 자동 저장 (기본: ON)
  - **자동 백업**: 주기적 백업
    - 옵션: OFF, 일 1회, 주 1회, 월 1회 (기본: 주 1회)
  - **백업 위치**: 기본값 %APPDATA%\eumcrawler\backups
  - **백업 유지 개수**: 최대 N개 유지 (기본: 10개)
  - 수동 백업 버튼

#### FR-08.4: UI 설정 (선택사항)
- **설명**: 사용자 인터페이스 커스터마이징
- **상세 요구사항**:
  - **테마**: 라이트 / 다크 (기본: 시스템 설정 따름)
  - **언어**: 한국어 / English (기본: 한국어)
  - **폰트 크기**: 작음 / 기본 / 크음 (기본: 기본)
  - **페이지네이션**: 페이지당 항목 수 (기본: 50, 선택: 10/25/50/100)

#### FR-08.5: 네트워크 설정 (선택사항)
- **설명**: 프록시 및 기타 네트워크 설정
- **상세 요구사항**:
  - **프록시 사용**: ON/OFF
  - **프록시 주소**: 프록시 서버 주소
  - **사용자 에이전트**: 기본값 또는 커스텀
  - 연결 테스트 버튼

#### FR-08.6: 정보 및 도움말
- **설명**: 애플리케이션 정보
- **상세 요구사항**:
  - **버전**: 현재 앱 버전
  - **업데이트 확인**: 새 버전 자동 확인 (선택사항)
  - **도움말**: 앱 내 도움말 또는 외부 문서 링크
  - **라이센스**: MIT 라이센스 정보
  - **로그 폴더**: 로그 폴더 열기 버튼

### FR-09: 대시보드

#### FR-09.1: 개요 통계
- **설명**: 주요 통계 정보를 한눈에 보기
- **상세 요구사항**:
  - **총 주소 수**: 관리 중인 총 주소 개수
  - **크롤링 완료**: 성공적으로 크롤링된 주소
  - **성공률**: (성공 수 / 전체) × 100%
  - **최근 활동**:
    - 오늘 크롤링된 주소 수
    - 이번 주 크롤링된 주소 수
    - 이번 달 크롤링된 주소 수
  - **캐시 통계**:
    - 전체 캐시 수
    - 유효한 캐시 수
    - 캐시 히트율 (마지막 100개 작업 기반)
  - **저장소 사용량**:
    - 총 사용 공간
    - 이미지 저장소
    - PDF 저장소

#### FR-09.2: 활동 차트 (선택사항)
- **설명**: 크롤링 활동을 차트로 시각화
- **상세 요구사항**:
  - **일일 활동**: 지난 7일간의 일일 크롤링 건수
  - **성공/실패율**: 파이 차트
  - **캐시 히트율 추이**: 지난 30일간의 추이

#### FR-09.3: 빠른 작업 버튼
- **설명**: 자주 사용하는 작업에 빠른 접근
- **상세 요구사항**:
  - **새 작업 만들기**: 주소 목록으로 이동
  - **Excel 가져오기**: 가져오기 다이얼로그 열기
  - **최근 작업 실행**: 마지막 작업 다시 실행 (같은 주소 목록)
  - **결과 보기**: 결과 목록으로 이동

#### FR-09.4: 최근 결과
- **설명**: 최근 크롤링한 결과를 미리보기
- **상세 요구사항**:
  - 최근 10개 결과 표시
  - 컬럼: 주소, PNU, 공시지가, 크롤링 일시
  - 클릭 시 결과 상세보기로 이동
  - "모두 보기" 링크로 전체 결과 목록으로 이동

---

## 비기능 요구사항 (Non-Functional Requirements)

### NFR-01: 성능

#### NFR-01.1: 처리 속도
- **요구사항**: 100개 주소를 15분 이내에 크롤링 완료
- **평균 처리 시간**: 주소당 5~10초 (네트워크 지연 포함)
- **UI 응답성**: 모든 사용자 작업에 대해 500ms 이내 응답
- **데이터 로드 시간**:
  - 주소 목록: 50개 로드 시 1초 이내
  - 결과 목록: 50개 로드 시 1초 이내
  - 대시보드: 2초 이내

#### NFR-01.2: 메모리 사용
- **최대 메모리**: 500MB (정상 작동)
- **메모리 누수**: 없음 (8시간 연속 작동 기준)
- **이미지 캐싱**: 최대 100개 썸네일만 메모리 보유

#### NFR-01.3: 데이터베이스 성능
- **쿼리 응답**: 95%의 쿼리가 100ms 이내
- **인덱싱**: 주소, PNU, 상태 필드에 인덱스 적용
- **배치 삽입**: 1000개 행 삽입 시 5초 이내

### NFR-02: 데이터 무결성

#### NFR-02.1: 데이터 손실 방지
- **요구사항**: 어떤 경우에도 데이터 손실 없음 (앱 충돌, 강제 종료 등)
- **구현**:
  - SQLite WAL (Write-Ahead Logging) 모드 사용
  - 각 크롤링 작업 후 즉시 DB 커밋
  - 트랜잭션 사용 (원자성 보장)

#### NFR-02.2: 데이터 일관성
- **외래 키 제약**: 활성화 (FK 무결성 보장)
- **동시성 제어**: 잠금 메커니즘 (여러 탭에서 동시 접근 가능하도록)
- **트랜잭션 격리**: SERIALIZABLE 또는 READ_COMMITTED

#### NFR-02.3: 백업 및 복구
- **자동 백업**: 설정에 따라 주기적 백업 (기본: 주 1회)
- **복구 기능**: 이전 백업에서 데이터 복구 가능
- **백업 검증**: 복구 전 백업 파일 무결성 확인

### NFR-03: 사용성 및 반응성

#### NFR-03.1: UI 반응성
- **요구사항**: 크롤링 중에도 UI는 항상 반응성 유지
- **구현**:
  - Tauri 백엔드에서 async 처리
  - UI는 메인 스레드 블로킹 없음
  - 진행 상황은 이벤트 기반 업데이트

#### NFR-03.2: 접근성
- **키보드 네비게이션**: 모든 기능을 키보드로 접근 가능
- **포커스 관리**: 논리적인 탭 순서
- **스크린 리더**: ARIA 레이블 (선택사항)

#### NFR-03.3: 다국어 지원
- **기본 언어**: 한국어
- **지원 언어**: 영어 (향후 확장 가능)
- **로컬라이제이션**: 날짜/시간 포맷, 숫자 포맷 등

### NFR-04: 저장소 및 확장성

#### NFR-04.1: 데이터베이스 크기
- **권장**: 100,000개 결과 이상 지원
- **데이터 압축**: 불필요한 필드는 저장하지 않음
- **정기 정리**: 오래된 데이터 아카이브 옵션 (선택사항)

#### NFR-04.2: 파일 저장소
- **권장**: 10GB 이상 디스크 공간
- **경고**: 저장소 부족 시 경고 표시 (1GB 이하)
- **정리 옵션**: 오래된 이미지/PDF 자동 삭제 옵션

#### NFR-04.3: 확장성
- **플러그인 아키텍처**: 향후 확장을 위한 구조 (선택사항)
- **다중 프로필**: 향후 지원 가능하도록 설계
- **API**: Tauri IPC를 통해 기능 확장 가능

### NFR-05: 보안성

#### NFR-05.1: 데이터 보호
- **디스크 암호화**: 민감 정보는 암호화 저장 (선택사항)
- **세션 관리**: 지정된 시간 후 자동 로그아웃 (해당 없음, 로컬 앱)
- **입력 검증**: 모든 사용자 입력 검증

#### NFR-05.2: 네트워크 보안
- **HTTPS**: 모든 HTTP 요청은 HTTPS 사용
- **인증서 검증**: SSL/TLS 인증서 검증
- **프록시 지원**: 기업 프록시 환경 지원

#### NFR-05.3: 애플리케이션 보안
- **코드 실행**: Tauri의 보안 모델 준수
- **데이터 격리**: 프로세스 간 데이터 격리
- **권한 관리**: 파일 시스템 접근 권한 최소화

### NFR-06: 호환성 및 플랫폼

#### NFR-06.1: 운영 체제
- **주요 지원**: Windows 10/11 (64-bit)
- **보조 지원**: macOS 11+ (Intel/Apple Silicon)
- **향후**: Linux (GTK) 지원 계획

#### NFR-06.2: 브라우저 기술
- **Chromium 기반**: Tauri가 제공하는 WebView 사용
- **최신 CSS/JS**: ES2020 이상 지원

#### NFR-06.3: 의존성
- **크롤러**: Playwright Chromium
- **데이터베이스**: SQLite 3.x
- **런타임**: Node.js 18+ (Bun 1.0+)

### NFR-07: 유지보수성

#### NFR-07.1: 코드 품질
- **언어**: TypeScript (타입 안정성)
- **포맷팅**: Prettier (일관된 코드 스타일)
- **린팅**: ESLint (코드 품질 확보)
- **테스트 커버리지**: 80% 이상

#### NFR-07.2: 문서화
- **API 문서**: Tauri 명령 명세서
- **사용자 문서**: 온라인 도움말
- **개발 가이드**: 기여자 가이드

#### NFR-07.3: 로깅
- **로그 레벨**: DEBUG, INFO, WARN, ERROR
- **로그 저장**: %APPDATA%\eumcrawler\logs
- **로그 로테이션**: 일일 또는 크기 기반 (10MB)

### NFR-08: 배포 및 설치

#### NFR-08.1: 설치 프로세스
- **설치 방식**: Windows MSI 또는 NSIS 인스톨러
- **설치 시간**: 1분 이내
- **사전 요구사항**: .NET Framework (필요 시) 또는 Visual C++ 재배포 가능 패키지
- **자동 설치**: 추가 단계 없음 (Playwright는 첫 실행 시 자동 다운로드)

#### NFR-08.2: 업그레이드
- **현재 위치 업그레이드**: 기존 설정 및 데이터 유지
- **버전 호환성**: 데이터베이스 마이그레이션 자동 수행
- **롤백**: 이전 버전으로 복원 가능

#### NFR-08.3: 제거
- **깔끔한 제거**: 앱 제거 시 임시 파일만 삭제 (데이터는 유지)
- **선택적 삭제**: 사용자가 데이터 삭제 여부 선택

---

## 데이터 모델

### 데이터베이스 스키마 (SQLite)

#### 테이블: addresses
주소 목록을 관리합니다.

```sql
CREATE TABLE addresses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address TEXT NOT NULL UNIQUE,
  group_id INTEGER,
  tags TEXT,  -- JSON 배열: ["tag1", "tag2"]
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (group_id) REFERENCES address_groups(id)
);

CREATE INDEX idx_addresses_group_id ON addresses(group_id);
CREATE INDEX idx_addresses_address ON addresses(address);
```

#### 테이블: address_groups
주소 그룹을 관리합니다.

```sql
CREATE TABLE address_groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  color TEXT,  -- 선택사항: 색상 표시용
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 테이블: crawl_results
크롤링 결과를 저장합니다.

```sql
CREATE TABLE crawl_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address_id INTEGER NOT NULL,
  pnu TEXT,  -- 지번번호
  present_addr TEXT,  -- 공시지번
  present_class TEXT,  -- 용도지역
  present_area TEXT,  -- 면적
  jiga TEXT,  -- 공시지가
  jiga_year TEXT,  -- 공시년도
  present_mark1 TEXT,  -- 표시1
  present_mark2 TEXT,  -- 표시2
  present_mark3 TEXT,  -- 표시3
  image_path TEXT,  -- 이미지 파일 경로 (상대 경로)
  pdf_path TEXT,  -- PDF 파일 경로 (상대 경로)
  status TEXT,  -- 'success', 'failed', 'partial'
  error_message TEXT,  -- 에러 메시지
  crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,  -- 캐시 만료 일시
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE
);

CREATE INDEX idx_crawl_results_address_id ON crawl_results(address_id);
CREATE INDEX idx_crawl_results_pnu ON crawl_results(pnu);
CREATE INDEX idx_crawl_results_status ON crawl_results(status);
CREATE INDEX idx_crawl_results_crawled_at ON crawl_results(crawled_at);
CREATE INDEX idx_crawl_results_expires_at ON crawl_results(expires_at);
```

#### 테이블: crawl_jobs
크롤링 작업을 관리합니다.

```sql
CREATE TABLE crawl_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT,  -- 'pending', 'running', 'paused', 'completed', 'cancelled'
  priority TEXT,  -- 'high', 'normal', 'low'
  total_count INTEGER,
  completed_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  skipped_count INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  started_at DATETIME,
  paused_at DATETIME,
  finished_at DATETIME
);

CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_priority ON crawl_jobs(priority);
CREATE INDEX idx_crawl_jobs_created_at ON crawl_jobs(created_at);
```

#### 테이블: job_items
작업 내의 개별 항목을 관리합니다.

```sql
CREATE TABLE job_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL,
  address_id INTEGER NOT NULL,
  result_id INTEGER,  -- 크롤링 결과 ID (NULL이면 아직 처리 안 됨)
  status TEXT,  -- 'pending', 'processing', 'completed', 'failed', 'skipped'
  order_num INTEGER,  -- 작업 순서
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
  FOREIGN KEY (address_id) REFERENCES addresses(id),
  FOREIGN KEY (result_id) REFERENCES crawl_results(id)
);

CREATE INDEX idx_job_items_job_id ON job_items(job_id);
CREATE INDEX idx_job_items_status ON job_items(status);
```

#### 테이블: settings
애플리케이션 설정을 저장합니다.

```sql
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  type TEXT,  -- 'string', 'integer', 'boolean', 'json'
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 기본 설정 항목
-- cache_expiry_days: 30 (정수)
-- default_scale: 1/2400 (문자열)
-- wait_time: 3 (정수, 초)
-- headless_mode: true (불린)
-- max_retries: 3 (정수)
-- page_load_timeout: 30 (정수, 초)
-- image_storage_path: (절대 경로)
-- pdf_storage_path: (절대 경로)
-- database_storage_path: (절대 경로)
-- auto_save_enabled: true (불린)
-- auto_backup_enabled: true (불린)
-- auto_backup_frequency: weekly (문자열)
-- theme: system (문자열, light/dark/system)
-- language: ko (문자열)
```

### 데이터 관계도

```
address_groups
    |
    v
addresses -- 1 to many --> job_items
    |                        |
    v                        v
crawl_results              crawl_jobs
    |
    +-- image_path (상대 경로)
    +-- pdf_path (상대 경로)
```

### 데이터 보존 정책

| 테이블 | 보존 기간 | 정리 주기 | 비고 |
|--------|---------|---------|------|
| addresses | 무한 | - | 사용자가 명시적으로 삭제하지 않는 한 유지 |
| address_groups | 무한 | - | 주소와 함께 관리 |
| crawl_results | 설정 가능 (기본 30일) | 주 1회 | expires_at 필드로 관리, 자동 정리 |
| crawl_jobs | 90일 | 월 1회 | 오래된 작업 이력 정리 |
| job_items | 90일 | 월 1회 | 완료된 작업의 항목 정리 |
| settings | 무한 | - | 사용자 설정 유지 |

---

## 사용자 인터페이스 요구사항

### UI 구조

#### 1. 메인 윈도우 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│ eumCrawler v2.0          [─][□][×]                               │
├─────────────────────────────────────────────────────────────────┤
│ [Dashboard] [주소] [결과] [작업] [설정]                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  메인 콘텐츠 영역 (탭별로 변경)                                    │
│                                                                   │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ 상태: 준비됨  └─────────────────────────┘  진행률: 0%            │
└─────────────────────────────────────────────────────────────────┘
```

#### 2. 주요 탭

1. **Dashboard 탭**: 대시보드 (기본값)
2. **주소 탭**: 주소 관리 (CRUD)
3. **결과 탭**: 크롤링 결과 조회
4. **작업 탭**: 배치 작업 관리
5. **설정 탭**: 애플리케이션 설정

### 화면 요구사항

#### Screen-1: Dashboard

**레이아웃**:
- 좌측: 통계 카드 (4열)
- 우측 상단: 빠른 작업 버튼
- 우측 중단: 활동 차트 (선택사항)
- 우측 하단: 최근 결과 목록

**컴포넌트**:
- 통계 카드: "총 주소", "완료율", "성공률", "캐시 효율"
- 빠른 버튼: "새 작업", "Excel 가져오기", "최근 작업 실행", "결과 보기"
- 최근 결과 테이블: 주소, PNU, 공시지가, 크롤링 일시

#### Screen-2: 주소 탭

**좌측 패널**:
- 그룹 목록
- 그룹 생성/수정/삭제 버튼

**우측 패널**:
- 검색 바
- 주소 목록 (테이블)
- 컬럼: ID, 주소, 태그, 상태, 생성일
- 다중 선택 체크박스
- 액션 버튼: "추가", "편집", "삭제", "크롤링"

**모달**:
- "주소 추가" 모달: 주소 입력, 태그 선택, 저장 버튼
- "주소 편집" 모달: 주소 수정, 태그 수정, 저장 버튼
- "그룹 관리" 모달: 그룹 생성/수정/삭제

#### Screen-3: 결과 탭

**상단 영역**:
- 검색 바 (주소, PNU, ID)
- 필터: 날짜 범위, 상태, 캐시 상태, 지역
- 정렬 옵션

**중앙 영역**:
- 결과 목록 (테이블)
- 컬럼: ID, 주소, PNU, 공시지가, 면적, 크롤링 일시, 상태
- 다중 선택 체크박스
- 페이지네이션

**우측 액션**:
- "상세보기", "강제 새로고침", "삭제", "내보내기" 버튼

**모달**:
- "상세보기" 모달: 모든 필드, 이미지 미리보기, PDF 링크

#### Screen-4: 작업 탭

**상단 영역**:
- "새 작업" 버튼
- 작업 큐 상태 표시 (실행 중 작업, 대기 중 작업 수)

**중앙 영역**:
- 현재 실행 중인 작업 (진행률 바, 상세 정보)
- "일시정지", "재개", "중단" 버튼

**하단 영역**:
- 작업 이력 (테이블)
- 컬럼: 작업명, 상태, 완료일, 전체/성공/실패 수, 소요 시간
- 페이지네이션

**모달**:
- "새 작업" 모달: 작업명, 소스 선택, 우선순위, 생성 버튼

#### Screen-5: 설정 탭

**좌측 메뉴**:
- 크롤러 설정
- 파일 저장소
- 자동 저장/백업
- UI 설정 (선택사항)
- 네트워크 설정 (선택사항)
- 정보

**우측 내용**:
- 각 메뉴별 설정 폼
- 저장 버튼
- 기본값으로 초기화 버튼

### 컬러 스킴

**라이트 테마**:
- 배경: #FFFFFF
- 텍스트: #000000
- 주요색: #007AFF
- 강조색: #FF3B30 (오류), #34C759 (성공), #FF9500 (경고)

**다크 테마**:
- 배경: #1C1C1E
- 텍스트: #FFFFFF
- 주요색: #0A84FF
- 강조색: #FF453A (오류), #30B0C0 (성공), #FF9500 (경고)

### 타이포그래피

- 제목: 16px, 600 weight
- 본문: 14px, 400 weight
- 작은 텍스트: 12px, 400 weight
- 코드: Monospace, 12px

---

## 통합 및 API

### Tauri 명령 (Command) 스펙

#### 주소 관리 명령

```rust
#[tauri::command]
async fn add_address(address: String, group_id: Option<i32>, tags: Option<Vec<String>>) -> Result<Address, String>

#[tauri::command]
async fn get_addresses(group_id: Option<i32>, skip: u32, take: u32) -> Result<Vec<Address>, String>

#[tauri::command]
async fn update_address(id: i32, address: String, group_id: Option<i32>, tags: Option<Vec<String>>) -> Result<Address, String>

#[tauri::command]
async fn delete_address(id: i32, cascade: bool) -> Result<(), String>

#[tauri::command]
async fn search_addresses(query: String, skip: u32, take: u32) -> Result<Vec<Address>, String>
```

#### 크롤링 명령

```rust
#[tauri::command]
async fn start_crawl_job(job: CrawlJobInput) -> Result<CrawlJob, String>

#[tauri::command]
async fn pause_crawl_job(job_id: i32) -> Result<(), String>

#[tauri::command]
async fn resume_crawl_job(job_id: i32) -> Result<(), String>

#[tauri::command]
async fn cancel_crawl_job(job_id: i32) -> Result<(), String>

#[tauri::command]
async fn get_job_status(job_id: i32) -> Result<CrawlJobStatus, String>
```

#### 결과 조회 명령

```rust
#[tauri::command]
async fn get_crawl_results(filter: ResultFilter, skip: u32, take: u32) -> Result<Vec<CrawlResult>, String>

#[tauri::command]
async fn get_result_detail(result_id: i32) -> Result<CrawlResultDetail, String>

#[tauri::command]
async fn export_results(format: String, result_ids: Vec<i32>, options: ExportOptions) -> Result<String, String>
```

#### 설정 명령

```rust
#[tauri::command]
async fn get_settings() -> Result<Settings, String>

#[tauri::command]
async fn update_settings(settings: Settings) -> Result<(), String>

#[tauri::command]
async fn get_setting(key: String) -> Result<String, String>

#[tauri::command]
async fn set_setting(key: String, value: String) -> Result<(), String>
```

### 이벤트 스트림 (Event-Driven)

프론트엔드는 Tauri 이벤트를 통해 실시간 업데이트를 수신합니다.

```typescript
// 크롤링 진행 상황
listen("crawl:progress", (event: CrawlProgressEvent) => {
  // {job_id, current_item, total_items, status, estimated_time}
})

// 크롤링 완료
listen("crawl:completed", (event: CrawlCompletedEvent) => {
  // {job_id, result}
})

// 크롤링 실패
listen("crawl:error", (event: CrawlErrorEvent) => {
  // {job_id, item_id, error_message}
})
```

---

## 보안 및 규정 준수

### 데이터 보안

1. **로컬 저장소**: 모든 데이터는 로컬 컴퓨터에 저장
   - 클라우드 전송 없음
   - 사용자의 전적인 제어

2. **입력 검증**:
   - 모든 사용자 입력 검증 (길이, 형식 등)
   - SQL 인젝션 방지 (PreparedStatement 사용)
   - XSS 방지 (출력 이스케이프)

3. **파일 접근 제어**:
   - 지정된 폴더만 접근 가능
   - 상대 경로 사용으로 경로 탈출 방지

### 네트워크 보안

1. **HTTPS**: eum.go.kr 통신은 HTTPS만 사용
2. **인증서 검증**: SSL/TLS 인증서 검증
3. **User-Agent**: 적절한 User-Agent 설정

### 라이센스

- **라이센스**: MIT License
- **의존성 라이센스**: Apache 2.0, MIT 등 모두 호환 가능

---

## 배포 및 유지보수

### 배포 프로세스

#### 단계 1: 개발 환경 준비
```bash
# Bun 설치
# Node.js 18+ 설치
# Rust 툴체인 설치
# Tauri CLI 설치: npm install -g @tauri-apps/cli
```

#### 단계 2: 빌드
```bash
bun run tauri build
# Output: src-tauri/target/release/eumcrawler.exe (Windows)
```

#### 단계 3: 패키징
- Windows MSI 생성 (Tauri의 NSIS 번들러 사용)
- 서명: 선택사항 (비용 발생)

#### 단계 4: 배포
- GitHub Releases에 업로드
- 사용자에게 다운로드 링크 제공
- 자동 업데이트: Tauri의 updater 기능 (선택사항)

### 업그레이드 전략

1. **마이너 업그레이드**: 버그 수정, 작은 기능
   - DB 마이그레이션 없음
   - 전체 재설치 불필요
   - 설정 유지

2. **메이저 업그레이드**: 큰 기능 추가, 아키텍처 변경
   - DB 마이그레이션 자동 수행
   - 사용자 알림 후 재설치 권장

### 유지보수 전략

1. **버그 리포팅**: GitHub Issues 또는 이메일
2. **버그 수정**: 심각도에 따라 패치 버전 업그레이드
3. **기능 요청**: GitHub Discussions 또는 이메일
4. **보안 업데이트**: 즉시 패치 (보안 이슈)

### 모니터링

1. **에러 로깅**: 로컬 로그 파일
   - 경로: %APPDATA%\eumcrawler\logs
   - 로테이션: 일일 또는 크기 기반

2. **성능 모니터링**: 선택사항
   - 크롤링 성능 통계
   - 평균 처리 시간, 성공률 등

---

## 범위 제외 (Out of Scope)

다음 항목들은 이 버전에 포함되지 않습니다. 향후 버전에서 검토됩니다.

1. **다중 사용자 / 서버 배포**
   - 로컬 데스크톱 앱 전용
   - 네트워크 공유 폴더는 미지원

2. **클라우드 동기화**
   - OneDrive, Google Drive, Dropbox 동기화 미지원
   - 로컬 저장소만 사용

3. **모바일 앱**
   - iOS, Android 앱 미지원
   - 향후 고려 가능

4. **실시간 협업**
   - 다중 사용자 동시 작업 미지원
   - 단일 사용자 기준

5. **자동 웹사이트 변경 감지**
   - eum.go.kr 구조 변경 시 수동 업데이트 필요
   - 선택자 변경은 개발자가 수정

6. **고급 분석 기능**
   - 데이터 시각화 (고급 차트)
   - 머신러닝 기반 분석
   - 향후 고려 가능

7. **국제화 (i18n)**
   - 현재: 한국어 기본
   - 향후: 다국어 지원 검토

8. **플러그인 시스템**
   - 확장성은 설계에 반영
   - 플러그인 로딩 메커니즘은 미지원

---

## 마이그레이션 전략

### Phase 1: 설계 및 기반 구축 (4주)

1. **프로젝트 구조 설정**
   - Tauri 프로젝트 초기화
   - Svelte 5 + Bun 설정
   - Git 저장소 설정

2. **데이터베이스 스키마**
   - SQLite 스키마 설계 (위 참조)
   - 마이그레이션 스크립트 작성

3. **Tauri 백엔드 기반**
   - 주요 Tauri 명령 구조 설계
   - 에러 처리 및 로깅 구조

### Phase 2: 핵심 기능 구현 (6주)

1. **주소 관리** (FR-01)
2. **크롤링 엔진** (FR-02)
3. **캐시 시스템** (FR-03)
4. **결과 관리** (FR-04)

### Phase 3: 부가 기능 (4주)

1. **이미지/PDF 관리** (FR-05)
2. **내보내기** (FR-06)
3. **배치 작업** (FR-07)
4. **설정** (FR-08)

### Phase 4: UI/UX 개선 (3주)

1. **대시보드** (FR-09)
2. **UI 폴리시 (테마, 접근성)**
3. **성능 최적화**

### Phase 5: 테스트 및 배포 (3주)

1. **단위 테스트**
2. **통합 테스트**
3. **E2E 테스트**
4. **배포 준비** (MSI 생성 등)

### 기존 v1.x 데이터 마이그레이션

```python
# v1.x Excel 파일 → v2.0 SQLite 변환
import openpyxl
import sqlite3

def migrate_excel_to_db(excel_file, db_file):
    # 1. Excel 읽기
    workbook = openpyxl.load_workbook(excel_file)
    worksheet = workbook.active

    # 2. SQLite 연결
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 3. 주소 및 결과 가져오기
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        address = row[1]  # B 컬럼
        if not address:
            break

        # addresses 테이블에 삽입
        cursor.execute(
            "INSERT INTO addresses (address) VALUES (?)",
            (address,)
        )
        address_id = cursor.lastrowid

        # crawl_results 테이블에 삽입 (C~J 컬럼)
        cursor.execute(
            """INSERT INTO crawl_results
            (address_id, pnu, present_addr, present_class, present_area, jiga,
             present_mark1, present_mark2, present_mark3, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (address_id, row[2], row[3], row[4], row[5], row[6],
             row[7], row[8], row[9], 'success')
        )

    conn.commit()
    conn.close()
```

---

## 성공 기준

### 기술적 성공 기준

- [ ] 모든 FR 요구사항 구현 완료 (FR-01 ~ FR-09)
- [ ] NFR 성능 기준 충족 (NFR-01 ~ NFR-03)
- [ ] 테스트 커버리지 80% 이상
- [ ] 런타임 메모리 사용량 500MB 이하 (정상 작동 시)
- [ ] 데이터베이스 쿼리 응답 100ms 이내 (95% 기준)
- [ ] 앱 시작 시간 3초 이내

### 사용자 경험 성공 기준

- [ ] 기존 v1.x 사용자의 만족도 8/10 이상
- [ ] 신규 사용자의 학습 곡선 30분 이내
- [ ] 기본 작업(크롤링 시작 ~ 결과 확인) 5분 이내 완료 가능
- [ ] UI/UX 모니터링: 사용자 피드백 기반 개선

### 배포 성공 기준

- [ ] Windows 10/11에서 설치 및 실행 성공률 99%
- [ ] 설치 크기 300MB 이하
- [ ] 자동 업그레이드 메커니즘 작동
- [ ] 기존 v1.x 데이터 마이그레이션 자동 수행

### 유지보수 성공 기준

- [ ] 코드 문서화: 모든 공개 함수/명령에 주석 포함
- [ ] 개발 가이드: 신규 기여자가 이해할 수 있는 문서 작성
- [ ] 로깅: 모든 중요 이벤트 로깅
- [ ] 버그 대응: 심각 버그 48시간 내 패치

---

## 승인 및 변경 이력

### 문서 승인

| 역할 | 이름 | 서명 | 날짜 |
|-----|-----|-----|------|
| 프로젝트 매니저 | - | - | 대기 중 |
| 기술 리더 | - | - | 대기 중 |
| 제품 오너 | - | - | 대기 중 |

### 변경 이력

| 버전 | 날짜 | 변경 사항 | 작성자 |
|-----|------|---------|--------|
| 1.0.0 | 2026-03-10 | 초안 작성 | Claude |

### 미래 검토 일정

- **다음 검토**: 2026-04-10 (Phase 1 완료 후)
- **최종 승인**: 2026-05-10 (Phase 5 완료 후)

---

**문서 끝**

---

## 부록: 기술 용어 정의

- **크롤링**: 웹사이트의 데이터를 자동으로 수집하는 프로세스
- **캐싱**: 이전에 조회한 데이터를 저장했다가 재사용하는 기법
- **PNU**: 지번 부여번호 (Parcel Number)
- **공시지가**: 국토교통부가 고시한 표준 지가
- **WAL (Write-Ahead Logging)**: 데이터베이스 안정성을 높이는 로깅 기법
- **Tauri**: Rust 기반의 경량 데스크톱 프레임워크
- **Svelte**: JavaScript 컴파일러 기반의 UI 프레임워크
- **Bun**: Node.js 호환 JavaScript 런타임
- **Playwright**: 브라우저 자동화 라이브러리

---

**이 문서는 기밀 문서입니다. 무단 배포를 금합니다.**
