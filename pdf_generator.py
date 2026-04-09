"""PDF generation logic for TOD (Immobilization Declaration) documents."""

import logging
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

from validators import TODRequest
import config

logger = logging.getLogger(__name__)


# Coordinate mappings for A4 template fields (in mm from bottom-left)
# A4 page: 210 x 297 mm
# Measured directly from template in Acrobat
FIELD_POSITIONS = {
    # Top section - Employee name, date, time
    "employeeName": (37, 250),        # Name field
    "date": (128, 250),               # Date field
    "time": (170, 250),               # Time field

    # Second row - Location and track number
    "location": (37, 240),            # Location field
    "trackNumber": (128, 240),        # Track number field

    # Train composition section - Vehicle number digits (5 boxes each)
    "firstVehicleDigits": [(37.54, 207), (45, 207), (52.42, 207), (60, 207), (73, 207)],
    "lastVehicleDigits": [(136.5, 207), (144, 207), (151.42, 207), (159, 207), (172, 207)],

    # Immobilization table (main data area)
    "table_x": 26,                      # Start X position
    "table_y": 157,                     # Start Y position (top of table)
    "table_row_height": 11,             # Height per row (mm)

    # Radio buttons section (right side)
    # End signals (Eindseinen)
    "endSignal_lamps": (177, 181),      # Lamps option
    "endSignal_plaques": (177, 166),    # Plaques option

    # Brake regime (Remregime)
    "brakeRegime_p": (177, 135),        # P option
    "brakeRegime_ll": (177, 117),       # LL option
    "brakeRegime_g": (177, 100),        # G option

    # Full brake test checkbox
    "fullBrakeTest": (165, 50),         # Checkbox

    # On-air indicator (white box above # sign)
    "isOnAir": (26, 178),               # NEE/JA checkbox
}


def mm2points(mm_value: float) -> float:
    """Convert millimeters to reportlab points (1mm = 2.834645669 points)."""
    return mm_value * mm


def _format_date_european(date_str: str) -> str:
    """Convert date from YYYY-MM-DD to DD-MM-YYYY format.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Date string in DD-MM-YYYY format
    """
    if not date_str:
        return ""

    try:
        # Parse YYYY-MM-DD format
        parts = date_str.split("-")
        if len(parts) == 3:
            year, month, day = parts
            return f"{day}-{month}-{year}"
    except Exception:
        pass

    return date_str


def load_template() -> PdfReader:
    """Load the TOD template PDF.

    Returns:
        PdfReader instance with template PDF

    Raises:
        FileNotFoundError: If template PDF doesn't exist
        Exception: If PDF is invalid
    """
    template_path = Path(config.TEMPLATE_PATH)

    if not template_path.exists():
        raise FileNotFoundError(
            f"TOD template not found at {template_path}. "
            f"Please ensure TOD.pdf exists in {template_path.parent}"
        )

    try:
        with open(template_path, "rb") as f:
            # Read bytes to keep PDF in memory after file closes
            pdf_bytes = f.read()
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        logger.debug(f"Loaded template: {template_path}")
        return pdf_reader
    except Exception as e:
        logger.error(f"Failed to load template: {e}")
        raise


def create_overlay(request: TODRequest) -> bytes:
    """Create overlay PDF with form data using reportlab.

    Args:
        request: Validated TODRequest with form data

    Returns:
        PDF bytes for overlay layer
    """
    # Create in-memory PDF
    buffer = BytesIO()

    # A4 size in points
    width, height = A4

    # Create canvas
    c = canvas.Canvas(buffer, pagesize=A4)

    try:
        # Set font
        c.setFont(config.PDF_FONT_FAMILY, config.PDF_FONT_SIZE_NORMAL)

        # Draw basic info fields
        _draw_text_field(c, request.employeeName, FIELD_POSITIONS["employeeName"])
        # Convert date to European format (DD-MM-YYYY)
        date_formatted = _format_date_european(request.date)
        _draw_text_field(c, date_formatted, FIELD_POSITIONS["date"])
        _draw_text_field(c, request.time, FIELD_POSITIONS["time"])
        _draw_text_field(c, request.location, FIELD_POSITIONS["location"])
        _draw_text_field(c, request.trackNumber, FIELD_POSITIONS["trackNumber"])

        # Draw vehicle numbers as individual digits in boxes
        _draw_vehicle_number_digits(c, request.firstVehicleNumber, FIELD_POSITIONS["firstVehicleDigits"])
        _draw_vehicle_number_digits(c, request.lastVehicleNumber, FIELD_POSITIONS["lastVehicleDigits"])

        # Draw on air status (only mark if JA/true)
        if request.isOnAir:
            _draw_on_air_checkbox(c, FIELD_POSITIONS["isOnAir"])

        # Draw immobilization table
        _draw_immobilization_table(c, request.immobilizationRows)

        # Draw radio buttons
        if request.endSignal:
            _draw_radio_buttons(
                c,
                FIELD_POSITIONS["endSignal_lamps"],
                FIELD_POSITIONS["endSignal_plaques"],
                request.endSignal == "lamps"
            )

        if request.brakeRegime:
            _draw_brake_regime_buttons(c, request.brakeRegime)

        # Full brake test checkbox
        if request.fullBrakeTest:
            _draw_checkbox(c, (165, 50), True)

        # Finalize
        c.save()
        buffer.seek(0)

        logger.debug("Overlay PDF created successfully")
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Failed to create overlay: {e}")
        raise


def _draw_vehicle_number_digits(c: canvas.Canvas, vehicle_number: str, positions: list):
    """Draw vehicle number as individual digits in separate boxes.

    Args:
        c: reportlab Canvas
        vehicle_number: Vehicle number string (e.g., "1 234-5")
        positions: List of (x_mm, y_mm) tuples for 5 digit boxes
    """
    if not vehicle_number:
        return

    # Extract only digits from vehicle number
    digits = ''.join(c_char for c_char in vehicle_number if c_char.isdigit())

    # Ensure we have exactly 5 digits
    if len(digits) < 5:
        digits = digits.ljust(5)  # Pad with spaces if needed
    else:
        digits = digits[:5]  # Truncate if too many

    c.setFont(config.PDF_FONT_FAMILY, config.PDF_FONT_SIZE_NORMAL)

    # Draw each digit in its box
    for i, digit in enumerate(digits):
        if i < len(positions):
            x, y = positions[i]
            x_pt = x * mm
            y_pt = y * mm
            c.drawString(x_pt, y_pt, digit)


def _draw_text_field(c: canvas.Canvas, text: str, position: tuple, font_size: int = None):
    """Draw text field at given position.

    Args:
        c: reportlab Canvas
        text: Text to draw
        position: (x_mm, y_mm) tuple
        font_size: Optional font size override
    """
    if not text:
        return

    x, y = position
    if font_size:
        c.setFont(config.PDF_FONT_FAMILY, font_size)

    # Convert mm to points (reportlab uses points, 1 inch = 72 points, 1 inch = 25.4 mm)
    x_pt = x * mm
    y_pt = y * mm

    c.drawString(x_pt, y_pt, str(text))


def _draw_immobilization_table(c: canvas.Canvas, rows: list):
    """Draw immobilization table.

    Args:
        c: reportlab Canvas
        rows: List of ImmobilizationRow objects
    """
    table_x_mm = FIELD_POSITIONS["table_x"]
    table_y = FIELD_POSITIONS["table_y"] * mm
    row_height = FIELD_POSITIONS["table_row_height"]

    # Vehicle digit positions relative to table_x (in mm)
    vehicle_digit_x_offsets = [11.54, 19, 26.42, 34, 47]

    c.setFont(config.PDF_FONT_FAMILY, 12)

    # Draw rows
    for row_idx, row in enumerate(rows):
        y = table_y - ((row_idx + 1) * row_height * mm)

        # Draw position (in mm, then convert to points)
        pos_x = table_x_mm * mm
        c.drawString(pos_x, y, str(row.position))

        # Draw vehicle number as 5 separate digits with exact spacing
        digits = ''.join(ch for ch in row.vehicleNumber if ch.isdigit())
        if len(digits) < 5:
            digits = digits.ljust(5)
        else:
            digits = digits[:5]

        for digit_idx, digit in enumerate(digits):
            digit_x = (table_x_mm + vehicle_digit_x_offsets[digit_idx]) * mm
            c.drawString(digit_x, y, digit)

        # Draw handrem, houten, metalen (skip if value is 0)
        handrem_x = (table_x_mm + 62) * mm
        houten_x = (table_x_mm + 78) * mm
        metalen_x = (table_x_mm + 99) * mm

        if row.handremCount > 0:
            c.drawString(handrem_x, y, str(row.handremCount))
        if row.woodenBlockCount > 0:
            c.drawString(houten_x, y, str(row.woodenBlockCount))
        if row.metalBlockCount > 0:
            c.drawString(metalen_x, y, str(row.metalBlockCount))


def _draw_radio_buttons(c: canvas.Canvas, lamps_pos: tuple, plaques_pos: tuple, selected_lamps: bool):
    """Draw radio buttons for end signal (Lamps vs Plaques).

    Args:
        c: reportlab Canvas
        lamps_pos: (x_mm, y_mm) position for Lamps button
        plaques_pos: (x_mm, y_mm) position for Plaques button
        selected_lamps: True if Lamps is selected, False if Plaques
    """
    # Draw X mark only for selected option
    c.setLineWidth(1.5)
    size = 3 * mm

    if selected_lamps:
        x, y = lamps_pos[0] * mm, lamps_pos[1] * mm
    else:
        x, y = plaques_pos[0] * mm, plaques_pos[1] * mm

    c.line(x - size/2, y - size/2, x + size/2, y + size/2)
    c.line(x - size/2, y + size/2, x + size/2, y - size/2)


def _draw_brake_regime_buttons(c: canvas.Canvas, regime: str):
    """Draw radio buttons for brake regime (P, LL, G).

    Args:
        c: reportlab Canvas
        regime: Selected regime ('P', 'LL', or 'G')
    """
    c.setLineWidth(1.5)
    size = 3 * mm

    positions = {
        "P": FIELD_POSITIONS["brakeRegime_p"],
        "LL": FIELD_POSITIONS["brakeRegime_ll"],
        "G": FIELD_POSITIONS["brakeRegime_g"],
    }

    for regime_key, pos in positions.items():
        if regime_key == regime:
            # Draw X mark for selected option
            x, y = pos[0] * mm, pos[1] * mm
            c.line(x - size/2, y - size/2, x + size/2, y + size/2)
            c.line(x - size/2, y + size/2, x + size/2, y - size/2)


def _draw_on_air_checkbox(c: canvas.Canvas, position: tuple):
    """Draw X mark for on-air status.

    Args:
        c: reportlab Canvas
        position: (x_mm, y_mm) position
    """
    x, y = position[0] * mm, position[1] * mm
    c.setLineWidth(1.5)
    size = 3 * mm
    c.line(x - size/2, y - size/2, x + size/2, y + size/2)
    c.line(x - size/2, y + size/2, x + size/2, y - size/2)


def _draw_checkbox(c: canvas.Canvas, position: tuple, checked: bool):
    """Draw checkbox.

    Args:
        c: reportlab Canvas
        position: (x_mm, y_mm) position
        checked: True to draw filled checkbox
    """
    x, y = position[0] * mm, position[1] * mm
    size = 3 * mm

    c.rect(x, y, size, size, fill=0)
    if checked:
        # Draw X with bold lines
        c.setLineWidth(1.5)
        c.line(x, y, x + size, y + size)
        c.line(x + size, y, x, y + size)


def generate_pdf(request: TODRequest) -> bytes:
    """Generate complete TOD PDF by merging template with overlay.

    Args:
        request: Validated TODRequest with form data

    Returns:
        Complete PDF as bytes

    Raises:
        Exception: If PDF generation fails
    """
    try:
        # Load template
        template_reader = load_template()

        # Create overlay
        overlay_bytes = create_overlay(request)
        overlay_reader = PdfReader(BytesIO(overlay_bytes))

        # Merge template with overlay
        writer = PdfWriter()
        template_page = template_reader.pages[0]
        overlay_page = overlay_reader.pages[0]

        # Merge overlay onto template
        template_page.merge_page(overlay_page)

        writer.add_page(template_page)

        # Write to bytes
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)

        logger.info(f"PDF generated for {request.employeeName} ({request.date})")
        return output_buffer.getvalue()

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise


def generate_pdf_filename(request: TODRequest) -> str:
    """Generate output filename for PDF.

    Format: TOD_{firstVehicleNumber}-{date}-{location}.pdf

    Args:
        request: TODRequest object

    Returns:
        Filename string
    """
    # Replace special characters in vehicle number and location
    vehicle = request.firstVehicleNumber.replace(" ", "").replace("-", "_")
    location = request.location.replace(" ", "_").replace("/", "_")

    filename = f"TOD_{vehicle}_{request.date}_{location}.pdf"
    return filename
