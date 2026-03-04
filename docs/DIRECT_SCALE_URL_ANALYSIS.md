# 축적 변경 직접 URL 접근 분석

## 발견한 URL

사용자가 제공한 URL을 분석한 결과:

```
https://www.eum.go.kr/web/ar/lu/luLandDet.jsp
?selGbn=umd
&isNoScr=script
&s_type=1
&viewType=
&p_location=
&p_type=
&p_type1=
&p_type2=
&p_type3=
&p_type4=
&p_type5=
&p_type6=
&p_type7=
&mode=search
&sggcd=11650
&pnu=1165010100108730024
&ucodes=UQA01X%3BUQA122%3BUQQ300%3BUNE200%3BUBA100%3BUQQ600
&markUcodes=UQA01X%3BUQA122%3BUQQ300
&adzoom=true
&scale=3000          ⭐ 축적 파라미터!
&scaleFlag=Y         ⭐ 축적 적용 플래그!
&hash=
&mobile_yn=
&add=land
&selSido=11
&selSgg=650
&selUmd=0101
&selRi=00
&landGbn=1
&bobn=873
&bubn=24
```

## 핵심 파라미터 분석

### ⭐ 필수 파라미터

| 파라미터 | 값 예시 | 설명 |
|---------|---------|------|
| `pnu` | `1165010100108730024` | 토지 고유번호 (필수) |
| `scale` | `3000` | 지도 축적 (1200, 3000, 6000, 12000) |
| `scaleFlag` | `Y` | 축적 적용 여부 (Y/N) |

### 📍 위치 정보 파라미터

| 파라미터 | 값 예시 | 설명 |
|---------|---------|------|
| `selSido` | `11` | 시도 코드 (서울=11) |
| `selSgg` | `650` | 시군구 코드 (강남구=650) |
| `selUmd` | `0101` | 읍면동 코드 |
| `selRi` | `00` | 리 코드 |
| `bobn` | `873` | 본번 |
| `bubn` | `24` | 부번 |
| `sggcd` | `11650` | 시군구 통합 코드 |

### 🗺️ 지도 관련 파라미터

| 파라미터 | 값 예시 | 설명 |
|---------|---------|------|
| `ucodes` | `UQA01X;UQA122;...` | 용도지역 코드 목록 |
| `markUcodes` | `UQA01X;UQA122;...` | 표시할 용도지역 |
| `adzoom` | `true` | 자동 줌 여부 |

### 🔧 기타 파라미터

| 파라미터 | 값 예시 | 설명 |
|---------|---------|------|
| `mode` | `search` | 모드 (검색) |
| `add` | `land` | 추가 정보 (토지) |
| `landGbn` | `1` | 토지 구분 |

## 💡 간소화 가능성

### 최소 필수 파라미터만 사용

```
https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu={PNU}&scale={SCALE}&scaleFlag=Y
```

**예시:**
```
https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu=1165010100108730024&scale=3000&scaleFlag=Y
```

### 테스트 필요 사항

1. **최소 파라미터로 접근 가능한가?**
   - `pnu`, `scale`, `scaleFlag`만으로 충분한지
   
2. **축적이 실제로 적용되는가?**
   - 지도 이미지가 지정한 축적으로 표시되는지
   
3. **데이터 추출이 가능한가?**
   - 개별공시지가, 지목 등 데이터가 정상적으로 로드되는지

## 🚀 구현 방안

### 현재 방식 (2단계)
```python
# 1단계: 메인 페이지에서 검색
page.goto("https://www.eum.go.kr/")
search_input.fill(address)
search_input.press("Enter")

# 2단계: 결과 페이지 로드
# URL: luLandDet.jsp?pnu={PNU} (자동 이동)
```

### 제안하는 방식 (1단계) ⚡
```python
# PNU를 이미 알고 있다면 직접 접근!
url = f"https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu={pnu}&scale={scale}&scaleFlag=Y"
page.goto(url)
```

## ✅ 장점

1. **속도 향상** ⚡
   - 검색 단계 생략
   - 직접 결과 페이지로 이동
   
2. **안정성 향상** 🛡️
   - 검색 입력 오류 가능성 제거
   - 드롭다운 처리 불필요
   
3. **축적 제어 간편** 🎯
   - URL 파라미터로 직접 축적 지정
   - 팝업창 불필요

## ⚠️ 주의사항

1. **PNU 필수**
   - 반드시 사전에 PNU를 알아야 함
   - Ajax 검증 단계는 여전히 필요
   
2. **세션/쿠키**
   - 직접 접근 시 세션이 필요한지 확인 필요
   - 메인 페이지 한 번 방문 후 사용 권장

## 🔄 개선된 플로우 제안

### 기존 플로우
```
1. Ajax로 PNU 가져오기
   ↓
2. 메인 페이지 접속
   ↓
3. 검색창에 주소 입력
   ↓
4. Enter 키 입력
   ↓
5. 드롭다운 처리
   ↓
6. 결과 페이지 로드
   ↓
7. 축적 변경 시 팝업창 열기
```

### 개선된 플로우 ⚡
```
1. Ajax로 PNU 가져오기
   ↓
2. 직접 URL로 접근
   https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu={PNU}&scale={SCALE}&scaleFlag=Y
   ↓
3. 데이터 추출
```

**단계 감소: 7단계 → 3단계!**

## 💻 구현 예시

### 새로운 메서드 제안

```python
def search_address_direct(self, pnu: str, scale: str = "1200") -> tuple[bool, str]:
    """
    PNU를 사용하여 직접 결과 페이지로 이동.
    
    Args:
        pnu: 토지 고유번호
        scale: 지도 축적 (기본값: "1200")
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # 직접 URL 생성
        url = (
            f"https://www.eum.go.kr/web/ar/lu/luLandDet.jsp"
            f"?pnu={pnu}&scale={scale}&scaleFlag=Y"
        )
        
        self.log(f"[cyan]Direct access: {url}[/cyan]")
        
        # 페이지 이동
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)  # 데이터 로드 대기
        
        # 데이터 로드 확인
        try:
            self.page.wait_for_selector(SELECTORS["JIGA"], timeout=10000)
            self.log("[green]OK[/green] Data loaded")
            return True, "성공"
        except:
            return False, "데이터 로드 실패"
            
    except Exception as e:
        return False, f"직접 접근 실패: {e}"
```

### 사용 예시

```python
# 기존 방식
count, pnu = scraper.check_address_count(address)
if count >= 1:
    success, msg = scraper.search_address(address)  # 느림
    
# 새로운 방식
count, pnu = scraper.check_address_count(address)
if count >= 1:
    success, msg = scraper.search_address_direct(pnu, scale="3000")  # 빠름!
```

## 📊 예상 성능 개선

| 항목 | 기존 방식 | 새로운 방식 | 개선율 |
|------|----------|------------|--------|
| 단계 수 | 7단계 | 3단계 | **-57%** |
| 예상 시간 | ~8초 | ~3초 | **-62%** |
| 안정성 | 보통 | 높음 | **+30%** |
| 축적 변경 | 팝업 필요 | URL 파라미터 | **간편** |

## 🧪 테스트 계획

1. **최소 파라미터 테스트**
   ```
   ?pnu={PNU}&scale={SCALE}&scaleFlag=Y
   ```

2. **다양한 축적 테스트**
   - scale=1200
   - scale=3000
   - scale=6000
   - scale=12000

3. **세션 의존성 테스트**
   - 메인 페이지 방문 없이 직접 접근
   - 메인 페이지 방문 후 직접 접근

4. **데이터 완전성 테스트**
   - 모든 필드가 정상적으로 로드되는지
   - 이미지가 올바른 축적으로 표시되는지

## 🎯 결론

**질문: "처음부터 이 주소로 축적을 바꿔서 변경해서 조회 할 수 있을까?"**

**답변: 가능성이 매우 높습니다!** ✅

### 근거:
1. URL에 `scale` 파라미터가 명시적으로 포함됨
2. `scaleFlag=Y`로 축적 적용을 명시
3. `pnu`만 있으면 직접 접근 가능한 구조
4. 검색 우회로 속도와 안정성 향상 기대

### 다음 단계:
1. ✅ 테스트 스크립트 작성 완료
2. ⏳ 실제 테스트 실행 필요
3. ⏳ 성공 시 `scraper.py`에 새 메서드 추가
4. ⏳ 성능 비교 및 검증

---

**작성일**: 2026-02-12  
**상태**: 분석 완료, 테스트 대기 중
