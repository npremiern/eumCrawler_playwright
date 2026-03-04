# 크롤링 URL 정보

## 📍 사용되는 URL들

### 1. 메인 페이지 (BASE_URL)
```
https://www.eum.go.kr/
```
- **용도**: 초기 접속, 주소 검색 시작
- **사용 시점**: 
  - 브라우저 시작 시
  - 각 주소 검색 전 (중복 데이터 방지)
- **코드 위치**: `config.py` 라인 11, `scraper.py` 라인 96, 197

---

## 🔍 PNU 가져오기 (주소 검증)

### 2. Ajax 검증 URL
```
POST https://www.eum.go.kr/web/am/mp/mpSearchAddrAjaxXml.jsp
```

**요청 파라미터:**
```python
{
    "sId": "selectAdAddrList",
    "keyword": "주소"  # 예: "서울특별시 강남구 테헤란로 152"
}
```

**헤더:**
```python
{
    "Referer": "https://www.eum.go.kr/",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.eum.go.kr",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}
```

**응답 형식:** XML
```xml
<?xml version="1.0" encoding="EUC-KR"?>
<root>
    <list>
        <pnu>1168010100100690000</pnu>
        <address>서울특별시 강남구 테헤란로 152</address>
        ...
    </list>
</root>
```

**코드 위치:** `scraper.py` 라인 81-177 (`check_address_count()` 메서드)

**주요 로직:**
1. Ajax POST 요청으로 주소 검색
2. XML 응답 파싱
3. `<pnu>` 태그에서 PNU 추출
4. 검색 결과 개수와 PNU 반환

---

## 🏠 실제 크롤링 URL

### 3. 주소 검색 (UI 방식)
```
https://www.eum.go.kr/
```

**검색 방법:**
1. 메인 페이지 접속
2. 검색창 (`#recent > input`)에 주소 입력
3. Enter 키 입력
4. 결과 페이지로 자동 이동

**결과 페이지 URL 예시:**
```
https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu=1168010100100690000
```

**코드 위치:** `scraper.py` 라인 178-259 (`search_address()` 메서드)

**주요 로직:**
1. BASE_URL로 이동 (라인 197)
2. 검색 입력창 찾기 (라인 202)
3. 주소 입력 (라인 208)
4. Enter 키 입력 (라인 212)
5. 드롭다운 결과가 있으면 첫 번째 클릭 (라인 220-228)
6. 결과 페이지 로드 대기 (라인 236)

---

## 🗺️ 이미지/PDF 다운로드 URL

### 4. 팝업 페이지 (축적 변경용)
```
https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu={PNU}&sMode=search&default_scale=3000&scale={SCALE}
```

**파라미터:**
- `pnu`: 토지 고유번호 (예: `1168010100100690000`)
- `sMode`: 검색 모드 (`search`)
- `default_scale`: 기본 축적 (`3000`)
- `scale`: 실제 적용할 축적 (예: `3000`, `6000`, `12000`)

**예시:**
```
# 1/3000 축적
https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu=1168010100100690000&sMode=search&default_scale=3000&scale=3000

# 1/6000 축적
https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu=1168010100100690000&sMode=search&default_scale=3000&scale=6000
```

**코드 위치:** 
- 이미지: `scraper.py` 라인 329
- PDF: `scraper.py` 라인 681

---

## 📊 전체 플로우

```
1. 시작
   ↓
   https://www.eum.go.kr/
   
2. PNU 가져오기 (Ajax)
   ↓
   POST https://www.eum.go.kr/web/am/mp/mpSearchAddrAjaxXml.jsp
   파라미터: { sId: "selectAdAddrList", keyword: "주소" }
   응답: XML (PNU 포함)
   
3. 실제 크롤링 (UI 검색)
   ↓
   https://www.eum.go.kr/
   → 검색창에 주소 입력 → Enter
   → 자동 이동
   ↓
   https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu={PNU}
   (결과 페이지)
   
4-1. 기본 축적 (1/1200)
   ↓
   결과 페이지에서 직접 이미지/PDF 추출
   
4-2. 변경된 축적 (1/3000+)
   ↓
   https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu={PNU}&scale={SCALE}
   (팝업 페이지에서 이미지/PDF 추출)
```

---

## 💻 코드 예시

### PNU 가져오기
```python
# scraper.py - check_address_count()
ajax_url = "https://www.eum.go.kr/web/am/mp/mpSearchAddrAjaxXml.jsp"
response = self.page.request.post(
    ajax_url,
    form={
        "sId": "selectAdAddrList",
        "keyword": "서울특별시 강남구 테헤란로 152"
    }
)
# XML 파싱하여 PNU 추출
# 결과: pnu = "1168010100100690000"
```

### 주소 검색
```python
# scraper.py - search_address()
self.page.goto("https://www.eum.go.kr/")
search_input = self.page.wait_for_selector("#recent > input")
search_input.fill("서울특별시 강남구 테헤란로 152")
search_input.press("Enter")
# 자동으로 결과 페이지로 이동
# URL: https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu=...
```

### 팝업 페이지 (축적 변경)
```python
# scraper.py - download_image_from_popup() / save_pdf_from_popup()
pnu = "1168010100100690000"
scale = "3000"
popup_url = f"https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu={pnu}&sMode=search&default_scale=3000&scale={scale}"
popup_page = self.context.new_page()
popup_page.goto(popup_url)
# 이미지 다운로드 또는 PDF 저장
```

---

## 🔑 핵심 포인트

1. **PNU는 Ajax로 먼저 가져옴** (검증 단계)
   - URL: `mpSearchAddrAjaxXml.jsp`
   - 방식: POST 요청
   - 응답: XML

2. **실제 크롤링은 UI 검색 사용** (데이터 추출 단계)
   - URL: 메인 페이지 → 자동 이동
   - 방식: 검색창 입력 + Enter
   - 결과: `luLandDet.jsp?pnu={PNU}`

3. **축적 변경은 팝업 페이지 사용**
   - URL: `luLandPop.jsp?pnu={PNU}&scale={SCALE}`
   - 용도: 이미지 다운로드, PDF 저장

---

## 📝 요약

| 단계 | URL | 메서드 | 용도 |
|------|-----|--------|------|
| **1. 메인** | `https://www.eum.go.kr/` | GET | 초기 접속 |
| **2. PNU 검증** | `POST /web/am/mp/mpSearchAddrAjaxXml.jsp` | POST | PNU 가져오기 |
| **3. 크롤링** | `https://www.eum.go.kr/` → 검색 | UI | 데이터 추출 |
| **4. 팝업** | `/web/ar/lu/luLandPop.jsp?pnu={PNU}&scale={SCALE}` | GET | 축적 변경 |
