# TOD PDF Coördinaten - Gemeten van Template Screenshot

## Afmetingen
- **PDF Pagina**: A4 (210 × 297 mm)
- **Oorsprong**: Bottom-left (PDF standaard)
- **Eenheid**: Millimeters (mm)

## Meetresultaten van Template

### Header Sectie
```
Zwarte balk: y = 270-297 mm
- LINEAS logo links
- Treinafbeelding + wagons in midden
- LINEAS logo rechts
- "14:30" (tijd) rechtsboven
- "T001" (spoor) rechtsboven
```

### Veld 1 - Medewerker / Collaborateur
- **Pictogram**: Persoon-icoon
- **Positie**:
  - X: ~15-20 mm van linker kant
  - Y: ~255-265 mm van onderkant

### Veld 2 - Datum / Date
- **Pictogram**: Kalender-icoon
- **Positie**:
  - X: ~95-105 mm
  - Y: ~255-265 mm

### Veld 3 - Tijd / Heure
- **Pictogram**: Klok-icoon
- **Positie**:
  - X: ~170-180 mm
  - Y: ~255-265 mm

### Veld 4 - Locatie / Lieu
- **Pictogram**: Locatie-pin icoon
- **Positie**:
  - X: ~15-20 mm
  - Y: ~245-255 mm

### Veld 5 - Spoor / Voie
- **Pictogram**: Spoor-icoon
- **Positie**:
  - X: ~95-105 mm
  - Y: ~245-255 mm

### Trein Compositie Section
```
Zwarte wagons (6x)
┌─────────────────────────────────────────┐
│ [Voertuig1] ... [Voertuig6]            │
│ [□ □ □ □] - [□]  ...  [□ □ □ □] - [□] │
└─────────────────────────────────────────┘

- Eerste voertuignummer (linkerkant): X: ~20 mm
- Puntjes in midden: X: ~100 mm
- Laatste voertuignummer (rechterkant): X: ~165 mm
- Y coördinaat: ~230-240 mm
```

### Immobilizatietabel (LEFT PANEL)
```
Header rij: Y ≈ 220 mm
- "Ftos" (Position): X ≈ 20 mm
- "Voertuig" (Vehicle): X ≈ 35 mm
- "Handrem": X ≈ 65 mm
- "Houten": X ≈ 90 mm
- "Metalen": X ≈ 115 mm

Data rijen: Y van 210 mm af, met -6mm per rij
Row 1: Y ≈ 210 mm
Row 2: Y ≈ 204 mm
Row 3: Y ≈ 198 mm
... tot Row 12: Y ≈ 138 mm
```

### Opties Paneel (RIGHT PANEL)
Rechts van tabel, beginnend rond X ≈ 140 mm

#### Eindseinen / Signaux
```
┌──────────────────────┐
│ [●]  Lamp  [ ] -    │  Y ≈ 205 mm
│ [ ]  Plaque [ ] -   │  Y ≈ 195 mm
└──────────────────────┘
```

#### Remregime / Régime
```
┌──────────────────────┐
│ [✓]  P      [ ]    │  Y ≈ 185 mm
│ [ ]  LL     [ ]    │  Y ≈ 175 mm
│ [ ]  G      [ ]    │  Y ≈ 165 mm
└──────────────────────┘
```

#### Remproef / Essai frein
```
┌──────────────────────┐
│  ⟷ (○)  [ ]         │  Y ≈ 150 mm
│  [●]              │  Y ≈ 140 mm
│  [ ]   [ ]  [ ]   │  Y ≈ 130 mm
└──────────────────────┘
```

---

## Voorgestelde FIELD_POSITIONS Update

```python
FIELD_POSITIONS = {
    # Basis informatie (top)
    "employeeName": (18, 260),
    "date": (100, 260),
    "time": (175, 260),

    # Tweede rij
    "location": (18, 250),
    "trackNumber": (100, 250),

    # Treinsamenstelling
    "firstVehicleNumber": (20, 235),
    "lastVehicleNumber": (165, 235),
    "isOnAir": (18, 215),  # JA/NEE checkbox

    # Immobilizatietabel
    "table_x": 18,
    "table_y": 210,
    "table_row_height": 6,

    # Rechtspaneel - Eindseinen
    "endSignal_lamps": (145, 205),     # ● radiobutton
    "endSignal_plaques": (145, 195),   # ● radiobutton

    # Rechtspaneel - Remregime
    "brakeRegime_p": (145, 185),       # ● radiobutton
    "brakeRegime_ll": (145, 175),      # ● radiobutton
    "brakeRegime_g": (145, 165),       # ● radiobutton

    # Rechtspaneel - Remproef
    "fullBrakeTest": (145, 140),       # ✓ checkbox
}
```

---

## Layout Zones

### Top Zone (Header met iconen)
- Y: 250-260 mm
- Bevat: Medewerker, Datum, Tijd, Locatie, Spoor

### Trein Zone (Compositie)
- Y: 230-240 mm
- Bevat: Eerste + Laatste voertuignummer

### Tabel Zone (Immobilizaties)
- Y: 138-210 mm
- Bevat: Max 12 rijen met voertuigdata

### Opties Zone (Rechtspaneel)
- Y: 130-205 mm
- Bevat: Eindseinen, Remregime, Remproef

### Footer Zone
- Y: 10-30 mm
- Bevat: "TOD v.3 - 12/2024"

---

## Tips voor Aanpassingen

1. **Schuifruimte**: ~2-3 mm tolerantie per veld
2. **Tabel rijen**: Afhankelijk van row_height (momenteel 6mm)
3. **Rechtspaneel**: Begint rond X = 140 mm
4. **Font size**: 10pt normaal, 8pt klein (voor tabel)
5. **Radio buttons**: ● teken is 2mm radius

---

## Volgende Stappen

1. Update FIELD_POSITIONS in `pdf_generator.py`
2. Test met `example_tod_input.json`
3. Verifieer elk veld in gegenereerde PDF
4. Verfijn coördinaten indien nodig (+/- 2mm per veld)
