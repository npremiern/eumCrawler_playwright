"""Test Korean filename support."""

from excel_handler import ExcelHandler

# Test with Korean filename
korean_file = "부동산데이터.xlsx"

print(f"Testing with Korean filename: {korean_file}")

try:
    handler = ExcelHandler(korean_file)
    if handler.open():
        print("✓ Successfully opened file with Korean filename")

        # Try reading data
        address = handler.read_address(2)
        print(f"✓ Read address from row 2: {address}")

        # Try writing data
        test_data = {
            "present_addr": "테스트 주소",
            "present_class": "대",
            "jiga": "1,000,000원"
        }
        handler.write_data(2, test_data)
        print("✓ Write data successful")

        # Try saving
        if handler.save():
            print("✓ Save successful")

        handler.close()
        print("\n✓ All operations successful with Korean filename!")
    else:
        print("✗ Failed to open file")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
