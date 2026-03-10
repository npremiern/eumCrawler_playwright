import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re

url = 'https://www.eum.go.kr/web/ar/lu/luLandDet.jsp'
params = {
            "selGbn": "umd",
            "isNoScr": "script",
            "s_type": "1",
            "mode": "search",
            "sggcd": "11650",
            "pnu": "1165010100108730024",
            "scale": "600",
            "scaleFlag": "Y"
}
data = urllib.parse.urlencode(params).encode('utf-8')
req = urllib.request.Request(url, data=data)
html = urllib.request.urlopen(req).read().decode('euc-kr', errors='ignore')
soup = BeautifulSoup(html, 'html.parser')

scripts = [s.get('src') for s in soup.find_all('script') if s.get('src')]
for s in scripts:
    s_url = urllib.parse.urljoin('https://www.eum.go.kr', s)
    try:
        content = urllib.request.urlopen(s_url).read().decode('utf-8', errors='ignore')
        if 'luLandDetPrintPop' in content:
            print("Found in:", s_url)
            for line in content.splitlines():
                if 'luLandDetPrintPop' in line:
                    print(line.strip())
        elif 'fn_printLayer' in content:
             print("Found fn_printLayer in:", s_url)
    except: pass
