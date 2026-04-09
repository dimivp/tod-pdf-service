"""Integration tests for PDF generation."""

import pytest
from io import BytesIO
from pathlib import Path

from validators import TODRequest
from pdf_generator import generate_pdf, generate_pdf_filename, load_template


class TestLoadTemplate:
    """Test template loading."""

    def test_template_exists(self):
        """Test that template file can be loaded."""
        template = load_template()
        assert template is not None
        assert len(template.pages) > 0

    def test_template_file_not_found(self, monkeypatch):
        """Test error handling when template doesn't exist."""
        import config
        monkeypatch.setattr(config, "TEMPLATE_PATH", Path("/nonexistent/path/TOD.pdf"))

        with pytest.raises(FileNotFoundError):
            load_template()


class TestPDFGeneration:
    """Test PDF generation."""

    def create_test_request(self) -> TODRequest:
        """Create a valid test request."""
        return TODRequest(
            employeeName="Test User",
            date="2026-04-09",
            time="14:30",
            location="Test Location",
            trackNumber="T001",
            firstVehicleNumber="1 234-5",
            lastVehicleNumber="1 234-9",
            isOnAir=True,
            immobilizationRows=[
                {
                    "position": 1,
                    "vehicleNumber": "1 234-5",
                    "handremCount": 2,
                    "woodenBlockCount": 4,
                    "metalBlockCount": 0,
                }
            ],
            endSignal="lamps",
            brakeRegime="P",
            fullBrakeTest=True,
        )

    def test_generate_pdf_basic(self):
        """Test basic PDF generation."""
        request = self.create_test_request()
        pdf_bytes = generate_pdf(request)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000  # Should be a reasonable size
        assert pdf_bytes[:4] == b"%PDF"  # PDF signature

    def test_generate_pdf_multiple_rows(self):
        """Test PDF generation with multiple immobilization rows."""
        request = self.create_test_request()
        request.immobilizationRows = [
            {
                "position": i,
                "vehicleNumber": f"1 {234+i:3d}-{i}",
                "handremCount": 2,
                "woodenBlockCount": 4,
                "metalBlockCount": 0,
            }
            for i in range(1, 6)
        ]

        pdf_bytes = generate_pdf(request)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_pdf_no_signals(self):
        """Test PDF generation without end signal or brake regime."""
        request = self.create_test_request()
        request.endSignal = None
        request.brakeRegime = None

        pdf_bytes = generate_pdf(request)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_filename(self):
        """Test filename generation."""
        request = self.create_test_request()
        filename = generate_pdf_filename(request)

        assert filename.startswith("TOD_")
        assert filename.endswith(".pdf")
        assert "2026-04-09" in filename
        assert "Test_Location" in filename


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
