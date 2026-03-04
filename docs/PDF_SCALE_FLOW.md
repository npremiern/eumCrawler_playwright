# 축적 변경 PDF 저장 플로우

## 📋 개요
축적을 변경한 후 PDF를 저장하면, 변경된 축적의 이미지가 PDF에 반영됩니다.

## 🔄 작동 방식

### 1. 기본 축적 (1/1200) - 메인 페이지 사용
```
주소 검색 → 결과 페이지 로드 → PDF 저장 (현재 페이지)
```
- **파일명 형식**: `{ID}_{주소}_1200.pdf`
- **예시**: `1_서울특별시강남구_1200.pdf`

### 2. 변경된 축적 (1/3000, 1/6000 등) - 팝업 페이지 사용
```
주소 검색 → PNU 획득 → 팝업창 열기 (축적 지정) → PDF 저장
```
- **파일명 형식**: `{ID}_{주소}_{축적}.pdf`
- **예시**: 
  - `1_서울특별시강남구_3000.pdf`
  - `1_서울특별시강남구_6000.pdf`

## 🎯 핵심 차이점

| 항목 | 기본 축적 (1/1200) | 변경된 축적 (1/3000+) |
|------|-------------------|---------------------|
| **페이지** | 메인 결과 페이지 | 팝업 페이지 |
| **URL** | 검색 결과 페이지 | `luLandPop.jsp?pnu={PNU}&scale={축적}` |
| **메서드** | `save_pdf()` | `save_pdf_from_popup()` |
| **축적 반영** | 기본값 | ✅ 지정한 축적 |

## 💻 코드 구조

### crawler.py (라인 491-500)
```python
# PDF 저장
if save_pdf:
    if scale == "1200":
        # 1/1200 축척: 메인 페이지에서 PDF 저장
        scraper.save_pdf(sequence_id, address)
    elif pnu:
        # 다른 축척: 팝업창에서 PDF 저장 (변경된 축적 반영!)
        scraper.save_pdf_from_popup(sequence_id, address, pnu, scale)
    else:
        # PNU 없으면 메인 페이지에서 저장
        scraper.save_pdf(sequence_id, address)
```

### scraper.py - save_pdf_from_popup()
```python
def save_pdf_from_popup(self, row: int, address: str, pnu: str, scale: str):
    """변경된 축적으로 PDF 저장"""
    # 1. 팝업 URL 생성 (축적 파라미터 포함)
    popup_url = f"https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu={pnu}&scale={scale}"
    
    # 2. 새 페이지에서 팝업 열기
    popup_page = self.context.new_page()
    popup_page.goto(popup_url)
    time.sleep(3)  # 지도 렌더링 대기
    
    # 3. PDF로 저장 (축적이 반영된 상태)
    pdf_path = f"{row}_{address}_{scale}.pdf"
    popup_page.pdf(path=pdf_path, format="A4")
    
    # 4. 팝업 닫기
    popup_page.close()
```

## 🧪 테스트 방법

### GUI에서 테스트
1. `crawler_gui.py` 실행
2. Excel 파일 선택
3. **축적 선택**: 드롭다운에서 `1/3000` 또는 `1/6000` 선택
4. **PDF 다운로드**: 체크박스 활성화
5. 크롤링 시작
6. `pdfs/` 폴더에서 결과 확인

### CLI에서 테스트
```bash
# 1/3000 축적으로 PDF 저장
python src/crawler.py -f example_data.xlsx --scale 3000

# 1/6000 축적으로 PDF 저장
python src/crawler.py -f example_data.xlsx --scale 6000
```

## 📁 결과 파일 위치
- **PDF 저장 경로**: `pdfs/`
- **이미지 저장 경로**: `images/`

## ✅ 확인 사항

### PDF가 올바르게 저장되었는지 확인
1. `pdfs/` 폴더 열기
2. 파일명에 축적 정보 확인 (예: `_3000.pdf`, `_6000.pdf`)
3. PDF 파일 열어서 지도 축적 확인
   - 1/3000: 더 넓은 범위
   - 1/6000: 훨씬 넓은 범위
   - 1/1200: 기본 범위 (가장 좁음)

### 로그에서 확인
크롤링 중 다음 메시지 확인:
```
[cyan]Opening popup for PDF: https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu=...&scale=3000[/cyan]
[cyan]Saving PDF to: pdfs/1_주소_3000.pdf[/cyan]
[green]OK[/green] PDF saved: pdfs/1_주소_3000.pdf
```

## 🔧 최근 수정 사항 (2026-02-12)

### 1. URL 수정
- **이전**: `{BASE_URL}/luLandPop.jsp?pnu={pnu}&scale={scale}`
- **수정**: `https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu={pnu}&sMode=search&default_scale=3000&scale={scale}`
- **이유**: 이미지 다운로드와 동일한 URL 형식 사용

### 2. 파일명에 축적 추가
- **이전**: `{ID}_{주소}.pdf`
- **수정**: `{ID}_{주소}_{축적}.pdf`
- **이유**: 어떤 축적으로 저장되었는지 파일명으로 구분 가능

## 🎨 시각적 플로우

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자가 축적 선택                          │
│                    (GUI 또는 CLI)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  축적 == "1200"?     │
              └──────────┬───────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼ YES                            ▼ NO
┌─────────────────┐              ┌──────────────────┐
│ 메인 페이지에서  │              │ 팝업 페이지 열기  │
│ PDF 저장        │              │ (축적 지정)      │
│                 │              │                  │
│ save_pdf()      │              │ URL:             │
│                 │              │ ?scale={축적}    │
│ 파일명:         │              │                  │
│ ID_주소_1200    │              │ save_pdf_from_   │
└─────────────────┘              │ popup()          │
                                 │                  │
                                 │ 파일명:          │
                                 │ ID_주소_{축적}   │
                                 └──────────────────┘
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │ 변경된 축적으로   │
                                 │ PDF 저장 완료!   │
                                 └──────────────────┘
```

## 📝 요약

**문제**: 축적을 변경하고 PDF를 저장하면 기본 축적으로 저장됨

**해결**: 
1. 축적이 1/1200이 아닌 경우 → 팝업창 사용
2. 팝업 URL에 `scale` 파라미터 포함
3. 팝업 페이지를 PDF로 저장
4. 파일명에 축적 정보 포함

**결과**: ✅ 변경된 축적이 PDF에 정확히 반영됨!
