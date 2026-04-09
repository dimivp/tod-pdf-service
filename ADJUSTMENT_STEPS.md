# TOD PDF Aanpassingen - Stap-voor-stap

## Probleem
De PDF wordt gegenereerd, maar de velden staan niet op de juiste plaats.

## Oorzaak
De coördinaten in `FIELD_POSITIONS` in `pdf_generator.py` zijn waarschijnlijk niet correct gealigneerd met de TOD template PDF.

## Oplossing

### Stap 1: Bepaal de juiste coördinaten in de template

```bash
# Ga naar je project directory
cd /Users/dimitrivanpraet/Documents/TOD

# Gebruik het coordinate finder script
python ../Desktop/pdf_coordinates.py TOD.pdf
```

Dit toont:
- **TEXT coordinates**: Huidige tekst in PDF (x, y van top-left)
- **RECTANGLES**: Velden in PDF (als form fields)

Output voorbeeld:
```
Text and Coordinates (from top-left)
Text                         X          Y          Width      Height
employeeName field          150.5      200.3      80.2       10.5
date field                  280.3      200.3      60.5       10.5
```

### Stap 2: Converteer coördinaten naar millimeters (bottom-left origin)

De script geeft coördinaten van top-left. Je moet ze converteren naar:
- **Origin**: bottom-left (PDF standaard)
- **Eenheid**: millimeters

**Formule:**
```
y_mm = 297 - (y_points / 2.834645669)
x_mm = x_points / 2.834645669
```

**Voorbeeld:**
```
Text script output: x=150.5, y=200.3
Omgerekend: x=53.1 mm, y=226.9 mm
```

### Stap 3: Update FIELD_POSITIONS

Open `tod-pdf-service/pdf_generator.py` en update:

```python
FIELD_POSITIONS = {
    # Update met je gemeten coördinaten
    "employeeName": (53.1, 226.9),      # WAS: (20, 270)
    "date": (98.8, 226.9),               # WAS: (20, 265)
    "time": (180.5, 226.9),              # WAS: (120, 265)
    # ... rest van de velden
}
```

### Stap 4: Test de PDF generatie

```bash
# Start Flask service (als niet al running)
cd /Users/dimitrivanpraet/Documents/TOD/tod-pdf-service
python app.py &

# Test met voorbeeld data
curl -X POST http://localhost:5000/generate-tod \
  -H "Content-Type: application/json" \
  -d @../example_tod_input.json \
  -o test_output.pdf

# Open de gegenereerde test_output.pdf en check posities
```

### Stap 5: Verfijn de posities

Herhaal stap 1-4 totdat alle velden correct gepositioneerd zijn.

## Voorbeeld Input Bestand

Zie: `example_tod_input.json`

```json
{
  "employeeName": "Jan Pieterzoon",
  "date": "2026-04-09",
  "time": "14:30",
  "location": "Antwerpen",
  "trackNumber": "T001",
  "firstVehicleNumber": "1 234-5",
  "lastVehicleNumber": "9 876-5",
  "isOnAir": false,
  "immobilizationRows": [
    {
      "position": 1,
      "vehicleNumber": "1 234-5",
      "handremCount": 2,
      "woodenBlockCount": 4,
      "metalBlockCount": 0
    }
  ],
  "endSignal": "lamps",
  "brakeRegime": "P",
  "fullBrakeTest": true
}
```

## Checklist Velden

Controleer dat alle velden correct staan:

- [ ] **employeeName** - Medewerker naam
- [ ] **date** - Datum (YYYY-MM-DD)
- [ ] **time** - Tijd (HH:mm)
- [ ] **location** - Locatie
- [ ] **trackNumber** - Spoor/Voie
- [ ] **firstVehicleNumber** - Eerste voertuig (X XXX-X)
- [ ] **lastVehicleNumber** - Laatste voertuig (X XXX-X)
- [ ] **isOnAir** - JA of NEE (op lucht)
- [ ] **Immobilizatie tabel** - 5 rijen met data
  - [ ] Position column
  - [ ] Vehicle number column
  - [ ] Handrem count
  - [ ] Wooden blocks
  - [ ] Metal blocks
- [ ] **endSignal** - ● op juiste plaats (lamps of plaques)
- [ ] **brakeRegime** - ● op juiste plaats (P, LL, of G)
- [ ] **fullBrakeTest** - ✓ checkbox ingevuld

## Troubleshooting

### Veld verschijnt niet
- Check of `FIELD_POSITIONS` het veld bevat
- Controleer of de coördinaten niet buiten de pagina liggen
- Check of het veld conditionally wordt getekend (bijv. `if request.endSignal`)

### Veld is op verkeerde plaats
- Herbepaal de coördinaten uit de PDF
- Check eenheid conversie (points → millimeters)
- Zorg dat je van bottom-left origin rekent

### Tekst is onleesbaar
- Check `PDF_FONT_FAMILY` en `PDF_FONT_SIZE_NORMAL` in config.py
- Controleer of veld niet buiten pagina getText

### Tabel rijen overlappen
- Controleer `table_row_height` (momenteel 6mm)
- Zorg dat `table_y` niet te laag is ingesteld

## Config Bestand

`config.py` bevat ook andere settings:

```python
PDF_FONT_FAMILY = "Helvetica"
PDF_FONT_SIZE_NORMAL = 10
PDF_FONT_SIZE_SMALL = 8
RADIO_BUTTON_RADIUS = 2  # mm
RADIO_BUTTON_FILL_RADIUS = 1  # mm
```

Pas deze aan voor betere weergave.

## Contactinfo

Als je vragen hebt, controleer:
1. FIELD_POSITIONING_GUIDE.md
2. pdf_generator.py comments
3. validators.py voor data structuur
