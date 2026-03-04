"""
Test if we can directly access the detail page with scale parameter.
축적 파라미터를 포함한 상세 페이지 직접 접근 테스트
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.sync_api import sync_playwright
import time

def test_direct_url_with_scale():
    """Test direct URL access with scale parameter"""
    
    # Example URL from user
    test_url = (
        "https://www.eum.go.kr/web/ar/lu/luLandDet.jsp"
        "?selGbn=umd&isNoScr=script&s_type=1&viewType=&p_location=&p_type="
        "&p_type1=&p_type2=&p_type3=&p_type4=&p_type5=&p_type6=&p_type7="
        "&mode=search&sggcd=11650&pnu=1165010100108730024"
        "&ucodes=UQA01X%3BUQA122%3BUQQ300%3BUNE200%3BUBA100%3BUQQ600"
        "&markUcodes=UQA01X%3BUQA122%3BUQQ300"
        "&adzoom=true&scale=3000&scaleFlag=Y&hash=&mobile_yn=&add=land"
        "&selSido=11&selSgg=650&selUmd=0101&selRi=00&landGbn=1&bobn=873&bubn=24"
    )
    
    print("=" * 80)
    print("축적 파라미터 포함 직접 URL 접근 테스트")
    print("Testing Direct URL Access with Scale Parameter")
    print("=" * 80)
    print(f"\n테스트 URL:\n{test_url}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        page = browser.new_page()
        
        print("1. 직접 URL 접근 중...")
        page.goto(test_url, wait_until="domcontentloaded")
        time.sleep(3)  # Wait for map to load
        
        print("2. 페이지 로드 완료")
        print(f"   현재 URL: {page.url}")
        
        # Check if scale is applied
        print("\n3. 축적 정보 확인 중...")
        
        # Try to find scale indicator on page
        scale_info = page.evaluate("""
            () => {
                // Look for scale dropdown or display
                const scaleSelect = document.querySelector('select[name="scale"]');
                if (scaleSelect) {
                    return {
                        found: true,
                        value: scaleSelect.value,
                        options: Array.from(scaleSelect.options).map(o => o.value)
                    };
                }
                
                // Look for scale in URL or page
                const url = window.location.href;
                const scaleMatch = url.match(/scale=(\\d+)/);
                
                return {
                    found: scaleMatch !== null,
                    value: scaleMatch ? scaleMatch[1] : null,
                    url: url
                };
            }
        """)
        
        print(f"   축적 정보: {scale_info}")
        
        # Check if map image is present
        print("\n4. 지도 이미지 확인 중...")
        img_selector = "#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img"
        
        try:
            img_element = page.wait_for_selector(img_selector, timeout=5000)
            img_src = img_element.get_attribute('src')
            print(f"   ✓ 지도 이미지 발견")
            print(f"   이미지 URL: {img_src[:100]}...")
            
            # Check if image URL contains scale info
            if 'scale' in img_src or '3000' in img_src:
                print(f"   ✓ 이미지 URL에 축적 정보 포함됨!")
            else:
                print(f"   ⚠ 이미지 URL에 축적 정보 없음")
                
        except Exception as e:
            print(f"   ✗ 지도 이미지 찾기 실패: {e}")
        
        # Check data fields
        print("\n5. 데이터 필드 확인 중...")
        jiga_selector = "xpath=//th[contains(text(), '개별공시지가')]/following-sibling::td"
        try:
            jiga = page.query_selector(jiga_selector)
            if jiga:
                print(f"   ✓ 개별공시지가: {jiga.inner_text().strip()[:50]}")
            else:
                print(f"   ✗ 개별공시지가 필드 없음")
        except Exception as e:
            print(f"   ✗ 데이터 필드 확인 실패: {e}")
        
        print("\n6. 5초 대기 (수동 확인용)...")
        time.sleep(5)
        
        print("\n" + "=" * 80)
        print("테스트 완료!")
        print("=" * 80)
        
        browser.close()

def test_simplified_url():
    """Test with minimal required parameters"""
    
    print("\n" + "=" * 80)
    print("간소화된 URL 테스트 (필수 파라미터만)")
    print("Testing Simplified URL (Required Parameters Only)")
    print("=" * 80)
    
    # Simplified URL with only essential parameters
    pnu = "1165010100108730024"
    scale = "3000"
    
    simple_url = f"https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu={pnu}&scale={scale}&scaleFlag=Y"
    
    print(f"\n간소화 URL:\n{simple_url}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("1. 간소화 URL 접근 중...")
        page.goto(simple_url, wait_until="domcontentloaded")
        time.sleep(3)
        
        print("2. 페이지 로드 완료")
        print(f"   현재 URL: {page.url}")
        
        # Check if it works
        print("\n3. 데이터 확인 중...")
        jiga_selector = "xpath=//th[contains(text(), '개별공시지가')]/following-sibling::td"
        try:
            jiga = page.query_selector(jiga_selector)
            if jiga:
                print(f"   ✓ 성공! 개별공시지가: {jiga.inner_text().strip()[:50]}")
                print(f"   ✓ 간소화된 URL로 직접 접근 가능!")
            else:
                print(f"   ✗ 데이터 로드 실패")
        except Exception as e:
            print(f"   ✗ 오류: {e}")
        
        print("\n4. 5초 대기...")
        time.sleep(5)
        
        browser.close()

def analyze_url_parameters():
    """Analyze the URL parameters"""
    
    print("\n" + "=" * 80)
    print("URL 파라미터 분석")
    print("URL Parameter Analysis")
    print("=" * 80)
    
    params = {
        "selGbn": "umd",
        "isNoScr": "script",
        "s_type": "1",
        "mode": "search",
        "sggcd": "11650",
        "pnu": "1165010100108730024",  # ⭐ 필수
        "ucodes": "UQA01X;UQA122;UQQ300;UNE200;UBA100;UQQ600",
        "markUcodes": "UQA01X;UQA122;UQQ300",
        "adzoom": "true",
        "scale": "3000",  # ⭐ 축적
        "scaleFlag": "Y",  # ⭐ 축적 플래그
        "add": "land",
        "selSido": "11",
        "selSgg": "650",
        "selUmd": "0101",
        "selRi": "00",
        "landGbn": "1",
        "bobn": "873",
        "bubn": "24"
    }
    
    print("\n핵심 파라미터:")
    print("  ⭐ pnu       : 토지 고유번호 (필수)")
    print("  ⭐ scale     : 축적 (예: 1200, 3000, 6000)")
    print("  ⭐ scaleFlag : 축적 적용 플래그 (Y/N)")
    
    print("\n위치 정보 파라미터:")
    print("  - selSido   : 시도 코드")
    print("  - selSgg    : 시군구 코드")
    print("  - selUmd    : 읍면동 코드")
    print("  - bobn      : 본번")
    print("  - bubn      : 부번")
    
    print("\n기타 파라미터:")
    print("  - ucodes    : 용도지역 코드")
    print("  - markUcodes: 표시할 용도지역")
    print("  - adzoom    : 자동 줌")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("\n[TEST] 축적 파라미터 직접 URL 접근 테스트\n")
    
    # Analyze parameters first
    analyze_url_parameters()
    
    # Test full URL
    input("\n전체 URL 테스트를 시작하려면 Enter를 누르세요...")
    test_direct_url_with_scale()
    
    # Test simplified URL
    input("\n간소화 URL 테스트를 시작하려면 Enter를 누르세요...")
    test_simplified_url()
    
    print("\n[OK] 모든 테스트 완료!")
