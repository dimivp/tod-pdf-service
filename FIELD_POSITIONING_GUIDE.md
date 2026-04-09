# TOD PDF Veldpositionering - Aanpassingsgids

## Voorbeeld Input Data

Zie `example_tod_input.json` voor een volledig ingevulde voorbeeld van TOD data die naar de Flask service wordt gestuurd.

## Huidige Veldposities (FIELD_POSITIONS in pdf_generator.py)

```python
FIELD_POSITIONS = {
    # Basis informatie
    "employeeName": (20, 270),      # Jan Pieterzoon
    "date": (20, 265),               # 2026-04-09
    "time": (120, 265),              # 14:30
    "location": (20, 260),           # Antwerpen
    "trackNumber": (120, 260),       # T001
    "firstVehicleNumber": (20, 255), # 1 234-5
    "lastVehicleNumber": (120, 255), # 9 876-5
    "isOnAir": (20, 250),            # JA/NEE

    # Immobilizatietabel
    "table_x": 20,
    "table_y": 180,
    "table_row_height": 6,

    # Radio buttons - Eindseinen
    "endSignal_lamps": (150, 160),    # ● (if endSignal == "lamps")
    "endSignal_plaques": (170, 160),  # ● (if endSignal == "plaques")

    # Radio buttons - Remregime
    "brakeRegime_p": (150, 150),      # ● (if brakeRegime == "P")
    "brakeRegime_ll": (170, 150),     # ● (if brakeRegime == "LL")
    "brakeRegime_g": (190, 150),      # ● (if brakeRegime == "G")
}
```

## Hoe de Veldposities Aanpassen

### Stap 1: Veldpositie bepalen
Gebruik het Python script in `/Users/dimitrivanpraet/Desktop/pdf_coordinates.py`:

```bash
cd /Users/dimitrivanpraet/Documents/TOD/tod-pdf-service
python ../../Desktop/pdf_coordinates.py TOD.pdf
```

Dit toont alle tekst en rechthoeken in de PDF met hun coördinaten.

### Stap 2: Coördinaten omzetten
- Het script toont coördinaten in punten (van top-left)
- De code gebruikt millimeters (van bottom-left)
- Formule: `y_mm = page_height_mm - y_points / 2.834645669`
- Voor een A4 pagina: `page_height_mm ≈ 297 mm`

### Stap 3: PDF aanpassen
1. Open `tod-pdf-service/pdf_generator.py`
2. Update de `FIELD_POSITIONS` dictionary met de juiste coördinaten
3. Test met het voorbeeld input bestand

## Test uitvoeren

```bash
cd /Users/dimitrivanpraet/Documents/TOD/tod-pdf-service

# Maak een test PDF met voorbeeld data
curl -X POST http://localhost:5000/generate-tod \
  -H "Content-Type: application/json" \
  -d @../example_tod_input.json \
  -o test_output.pdf
```

## Debuggen met visual markers

Voeg visuele markers toe in de PDF voor debugging:

```python
# In pdf_generator.py, voeg dit toe voor debugging:
def _draw_debug_marker(c: canvas.Canvas, position: tuple, label: str):
    """Draw a debug marker at a position"""
    x, y = position[0] * mm, position[1] * mm
    # Draw small red circle
    c.setStrokeColor(colors.red)
    c.circle(x, y, 2 * mm, fill=0)
    # Draw label
    c.setFont("Helvetica", 6)
    c.drawString(x + 3 * mm, y, label)
```

## Veldtype referentie

| Veld | Type | Voorbeeld |
|------|------|-----------|
| employeeName | tekst | "Jan Pieterzoon" |
| date | tekst (YYYY-MM-DD) | "2026-04-09" |
| time | tekst (HH:mm) | "14:30" |
| location | tekst | "Antwerpen" |
| trackNumber | tekst | "T001" |
| firstVehicleNumber | tekst (X XXX-X) | "1 234-5" |
| lastVehicleNumber | tekst (X XXX-X) | "9 876-5" |
| isOnAir | JA of NEE | false → "NEE" |
| immobilizationRows | tabel (max 12 rijen) | zie voorbeeld |
| endSignal | radio (● teken) | "lamps" of "plaques" |
| brakeRegime | radio (● teken) | "P", "LL", of "G" |
| fullBrakeTest | checkbox (✓) | true/false |

## Immobilizatietabel Structuur

```
Header: Pos | Voertuig | Handrem | Houten | Metalen
Row 1:  1   | 1 234-5  | 2       | 4      | 0
Row 2:  2   | 2 345-6  | 1       | 2      | 0
...max 12 rows
```

## Tips

1. **Gebruik millimeters**: Alle coördinaten in pdf_generator.py zijn in mm
2. **Y-coördinaat**: Groter getal = hoger op pagina
3. **Tabel rijen**: Automatisch berekend op basis van `table_y` en `table_row_height`
4. **Radio buttons**: Teken alleen als waarde is ingesteld
5. **Font size**: `PDF_FONT_SIZE_NORMAL = 10`, `PDF_FONT_SIZE_SMALL = 8`

## Referentie PDF

Original TOD template: `/Users/dimitrivanpraet/Documents/TOD/TOD.pdf`

Controleer de template voor de exacte lay-out van alle velden.
