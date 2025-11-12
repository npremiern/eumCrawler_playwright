"""Test image download to see what we're getting."""

import requests
from PIL import Image
from io import BytesIO

# Test URL from the error message
test_url = "https://www.eum.go.kr/web/ar/lu/images?key=1762881738199-2635010500106200003"

print(f"Testing download from: {test_url}")

try:
    response = requests.get(test_url, timeout=30)
    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content-Length: {response.headers.get('content-length')} bytes")

    # Check first few bytes
    first_bytes = response.content[:100]
    print(f"First bytes: {first_bytes[:50]}")

    # Check if it's HTML (error page)
    if b'<html' in response.content[:200].lower() or b'<!doctype' in response.content[:200].lower():
        print("\n✗ Response is HTML (probably an error page)")
        print("First 500 chars of response:")
        print(response.text[:500])
    else:
        # Try to open as image
        try:
            img = Image.open(BytesIO(response.content))
            print(f"\n✓ Valid image!")
            print(f"  Format: {img.format}")
            print(f"  Size: {img.size}")
            print(f"  Mode: {img.mode}")
        except Exception as e:
            print(f"\n✗ Cannot open as image: {e}")
            print("Saving to test_download.bin for inspection...")
            with open("test_download.bin", "wb") as f:
                f.write(response.content)
            print("✓ Saved to test_download.bin")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
