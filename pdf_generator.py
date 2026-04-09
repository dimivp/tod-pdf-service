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
# Calibrated from actual TOD.pdf template screenshot
FIELD_POSITIONS = {
    # Top section - Medewerker/Collaborateur row (below header)
    "employeeName": (18, 260),

    # Top section - Datum/Date and Tijd/Heure
    "date": (100, 260),
    "time": (175, 260),

    # Second row - Locatie/Lieu and Spoor/Voie
    "location": (18, 250),
    "trackNumber": (100, 250),

    # Train composition - Voertuignummers/Numéros de véhicule
    "firstVehicleNumber": (20, 235),
    "lastVehicleNumber": (165, 235),

    # On-air checkbox
    "isOnAir": (18, 215),

    # Immobilization table (left panel) - max 12 rows
    "table_x": 18,
    "table_y": 210,
    "table_row_height": 6,

    # Radio buttons - Eindseinen/Signaux (right panel)
    "endSignal_lamps": (145, 205),
    "endSignal_plaques": (145, 195),

    # Radio buttons - Remregime/Régime (right panel)
    "brakeRegime_p": (145, 185),
    "brakeRegime_ll": (145, 175),
    "brakeRegime_g": (145, 165),

    # Full brake test checkbox (right panel)
    "fullBrakeTest": (145, 140)
}


def mm2points(mm_value: float) -> float:
    """Convert millimeters to reportlab points (1mm = 2.834645669 points)."""
    return mm_value * mm


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

        # DEBUG: Draw position markers (red circles)
        c.setStrokeColor(colors.red)
        c.setLineWidth(0.5)
        for label, pos in [
            ("NAME", FIELD_POSITIONS["employeeName"]),
            ("DATE", FIELD_POSITIONS["date"]),
            ("TIME", FIELD_POSITIONS["time"]),
            ("LOC", FIELD_POSITIONS["location"]),
            ("TRACK", FIELD_POSITIONS["trackNumber"]),
            ("VEH1", FIELD_POSITIONS["firstVehicleNumber"]),
            ("VEH2", FIELD_POSITIONS["lastVehicleNumber"]),
        ]:
            x, y = pos[0] * mm, pos[1] * mm
            c.circle(x, y, 3 * mm, fill=0)
            c.setFont("Helvetica", 6)
            c.drawString(x + 4 * mm, y, label)

        # Draw basic info fields
        _draw_text_field(c, request.employeeName, FIELD_POSITIONS["employeeName"])
        _draw_text_field(c, request.date, FIELD_POSITIONS["date"])
        _draw_text_field(c, request.time, FIELD_POSITIONS["time"])
        _draw_text_field(c, request.location, FIELD_POSITIONS["location"])
        _draw_text_field(c, request.trackNumber, FIELD_POSITIONS["trackNumber"])
        _draw_text_field(c, request.firstVehicleNumber, FIELD_POSITIONS["firstVehicleNumber"])
        _draw_text_field(c, request.lastVehicleNumber, FIELD_POSITIONS["lastVehicleNumber"])

        # Draw on air status
        status_text = "JA" if request.isOnAir else "NEE"
        _draw_text_field(c, status_text, FIELD_POSITIONS["isOnAir"])

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
            _draw_checkbox(c, (150, 140), True)

        # Finalize
        c.save()
        buffer.seek(0)

        logger.debug("Overlay PDF created successfully")
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Failed to create overlay: {e}")
        raise


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
    table_x = FIELD_POSITIONS["table_x"] * mm
    table_y = FIELD_POSITIONS["table_y"] * mm
    row_height = FIELD_POSITIONS["table_row_height"]

    # Column widths (in points)
    col_widths = [10 * mm, 20 * mm, 15 * mm, 20 * mm, 20 * mm]

    # Headers
    headers = ["Pos", "Voertuig", "Handrem", "Houten", "Metalen"]

    # Prepare table data
    table_data = [headers]
    for row in rows:
        table_data.append([
            str(row.position),
            row.vehicleNumber,
            str(row.handremCount),
            str(row.woodenBlockCount),
            str(row.metalBlockCount),
        ])

    # Create table (for accurate sizing and alignment)
    # Note: reportlab Tables are complex, so we'll draw rows manually for better control
    c.setFont(config.PDF_FONT_FAMILY, config.PDF_FONT_SIZE_SMALL)

    # Draw headers
    for i, header in enumerate(headers):
        x = table_x + (i * col_widths[i])
        c.drawString(x, table_y, header)

    # Draw rows
    for row_idx, row in enumerate(rows):
        y = table_y - ((row_idx + 1) * row_height * mm)
        c.drawString(table_x, y, str(row.position))
        c.drawString(table_x + col_widths[0], y, row.vehicleNumber)
        c.drawString(table_x + col_widths[0] + col_widths[1], y, str(row.handremCount))
        c.drawString(table_x + col_widths[0] + col_widths[1] + col_widths[2], y, str(row.woodenBlockCount))
        c.drawString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y, str(row.metalBlockCount))


def _draw_radio_buttons(c: canvas.Canvas, lamps_pos: tuple, plaques_pos: tuple, selected_lamps: bool):
    """Draw radio buttons for end signal (Lamps vs Plaques).

    Args:
        c: reportlab Canvas
        lamps_pos: (x_mm, y_mm) position for Lamps button
        plaques_pos: (x_mm, y_mm) position for Plaques button
        selected_lamps: True if Lamps is selected, False if Plaques
    """
    radius = config.RADIO_BUTTON_RADIUS
    fill_radius = config.RADIO_BUTTON_FILL_RADIUS

    # Convert to points
    lamps_x, lamps_y = lamps_pos[0] * mm, lamps_pos[1] * mm
    plaques_x, plaques_y = plaques_pos[0] * mm, plaques_pos[1] * mm

    # Draw circles
    c.circle(lamps_x, lamps_y, radius, fill=0)
    c.circle(plaques_x, plaques_y, radius, fill=0)

    # Fill selected radio button
    if selected_lamps:
        c.circle(lamps_x, lamps_y, fill_radius, fill=1)
    else:
        c.circle(plaques_x, plaques_y, fill_radius, fill=1)


def _draw_brake_regime_buttons(c: canvas.Canvas, regime: str):
    """Draw radio buttons for brake regime (P, LL, G).

    Args:
        c: reportlab Canvas
        regime: Selected regime ('P', 'LL', or 'G')
    """
    radius = config.RADIO_BUTTON_RADIUS
    fill_radius = config.RADIO_BUTTON_FILL_RADIUS

    positions = {
        "P": FIELD_POSITIONS["brakeRegime_p"],
        "LL": FIELD_POSITIONS["brakeRegime_ll"],
        "G": FIELD_POSITIONS["brakeRegime_g"],
    }

    for regime_key, pos in positions.items():
        x, y = pos[0] * mm, pos[1] * mm
        c.circle(x, y, radius, fill=0)

        if regime_key == regime:
            c.circle(x, y, fill_radius, fill=1)


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
        # Draw X
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
