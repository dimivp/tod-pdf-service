#!/usr/bin/env python3
"""Quick integration test for TOD PDF Service."""

import sys
import json
from pathlib import Path

# Test imports
try:
    from validators import TODRequest, ImmobilizationRow
    from pdf_generator import generate_pdf, generate_pdf_filename, load_template
    from app import app
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 1: Validators
print("\n[Test 1] Validators")
try:
    with open("tests/sample_input.json") as f:
        data = json.load(f)
    request = TODRequest(**data)
    print(f"✓ Valid TOD request created for {request.employeeName}")
except Exception as e:
    print(f"✗ Validation failed: {e}")
    sys.exit(1)

# Test 2: Template Loading
print("\n[Test 2] Template Loading")
try:
    template = load_template()
    pages = len(template.pages)
    print(f"✓ Template loaded ({pages} pages)")
except Exception as e:
    print(f"✗ Template loading failed: {e}")
    sys.exit(1)

# Test 3: PDF Generation
print("\n[Test 3] PDF Generation")
try:
    pdf_bytes = generate_pdf(request)
    print(f"✓ PDF generated ({len(pdf_bytes)} bytes)")
    print(f"  PDF signature: {pdf_bytes[:4]}")
except Exception as e:
    print(f"✗ PDF generation failed: {e}")
    sys.exit(1)

# Test 4: Filename Generation
print("\n[Test 4] Filename Generation")
try:
    filename = generate_pdf_filename(request)
    print(f"✓ Filename generated: {filename}")
except Exception as e:
    print(f"✗ Filename generation failed: {e}")
    sys.exit(1)

# Test 5: Flask App
print("\n[Test 5] Flask App")
try:
    client = app.test_client()

    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    health_data = response.get_json()
    print(f"✓ Health check passed: {health_data['status']}")

    # PDF generation endpoint
    response = client.post(
        "/generate-tod",
        json=data,
        content_type="application/json"
    )
    if response.status_code == 200:
        pdf_data = response.get_data()
        print(f"✓ PDF endpoint works ({len(pdf_data)} bytes)")
    else:
        print(f"✗ PDF endpoint returned {response.status_code}")
        print(f"  Response: {response.get_json()}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Flask app test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("✓ All tests passed!")
print("="*50)
