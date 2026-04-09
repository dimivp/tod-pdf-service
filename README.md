# TOD PDF Service

Standalone PDF generation service voor TOD (Immobilization Declaration) documenten. Genereert PDFs op basis van JSON input door data over te plaatsen op de TOD template.

## Features

- **REST API** - HTTP POST endpoint voor PDF generatie
- **Input Validation** - Pydantic models voor strict input validation
- **PDF Overlay** - Merge van form data met template PDF
- **MinIO Integration** - Optioneel: uploads generated PDFs naar MinIO S3
- **Health Check** - Coolify-compatible health endpoint
- **Error Handling** - Comprehensive error logging & responses
- **Immobilization Table** - Support voor max 12 rows
- **Radio Buttons** - Eindseinen (Lamps/Plaques) en Remregime (P/LL/G)

## Requirements

- Python 3.10+
- Flask 3.0+
- pypdf 3.17+
- reportlab 4.0+
- boto3 1.28+ (for MinIO, optional)

## Setup

### 1. Local Development

```bash
cd tod-pdf-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and configure
cp .env.example .env

# Run development server
python app.py
```

Server runs on `http://localhost:5000`

### 2. Docker Setup

```bash
# Build image
docker build -t tod-pdf-service .

# Run container
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e LOG_LEVEL=INFO \
  tod-pdf-service
```

### 3. Docker Compose (with local MinIO)

```bash
docker-compose up -d

# Accessible at:
# - PDF Service: http://localhost:5000
# - MinIO Console: http://localhost:9001
#   Username: minioadmin
#   Password: minioadmin
```

## API Usage

### Health Check

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "ok",
  "service": "tod-pdf-service",
  "version": "1.0.0",
  "minio_enabled": true
}
```

### Generate TOD PDF

```bash
curl -X POST http://localhost:5000/generate-tod \
  -H "Content-Type: application/json" \
  -d @tests/sample_input.json \
  --output generated.pdf
```

### Request Body

```json
{
  "employeeName": "Jan Pieterse",
  "date": "2026-04-09",
  "time": "14:30",
  "location": "Antwerpen",
  "trackNumber": "T001",
  "firstVehicleNumber": "1 234-5",
  "lastVehicleNumber": "1 234-9",
  "isOnAir": true,
  "tripId": "TRIP-20260409-001",
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

### Response

On success (200):
- Returns PDF file as binary attachment
- Filename: `TOD_{vehicle}_{date}_{location}.pdf`

On validation error (400):
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "date",
      "message": "Invalid date format: 09-04-2026. Expected YYYY-MM-DD"
    }
  ]
}
```

On server error (500):
```json
{
  "error": "PDF generation failed",
  "message": "Error details...",
  "request_id": "a1b2c3d4"
}
```

## Configuration

### Environment Variables

```env
# Flask
FLASK_ENV=production              # development|production
LOG_LEVEL=INFO                    # DEBUG|INFO|WARNING|ERROR

# MinIO (optional)
MINIO_ENDPOINT=s3.dimivp.be      # MinIO server address
MINIO_ACCESS_KEY=...             # Access key
MINIO_SECRET_KEY=...             # Secret key
MINIO_BUCKET=logboek-pdfs        # Bucket name
```

## Testing

### Unit Tests

```bash
pip install pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_validators.py -v
```

### Manual Testing

```bash
# Use sample JSON
curl -X POST http://localhost:5000/generate-tod \
  -H "Content-Type: application/json" \
  -d @tests/sample_input.json \
  --output test_output.pdf

# Verify PDF
open test_output.pdf  # On macOS
```

## Troubleshooting

### PDF Not Generated

Check logs for errors:
```bash
docker logs tod-pdf-service  # if running in Docker
```

Common issues:
- Missing template: Ensure `templates/TOD.pdf` exists
- Invalid JSON: Run through validator with verbose output
- MinIO offline: Service continues working without S3 upload

### Field Alignment Issues

If overlaid text doesn't align with template:

1. Open the template PDF
2. Measure field positions (in mm from bottom-left)
3. Update `FIELD_POSITIONS` in `pdf_generator.py`
4. Regenerate and verify

## Deployment to Coolify

### 1. Create Git Repository

```bash
cd tod-pdf-service
git init
git add .
git commit -m "Initial commit: TOD PDF Service"
```

### 2. Push to Remote

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

### 3. Configure in Coolify

1. Go to Coolify dashboard
2. Create new Service → Docker
3. Set git repository URL
4. Configure environment variables:
   - `FLASK_ENV=production`
   - `LOG_LEVEL=INFO`
   - `MINIO_ENDPOINT=s3.dimivp.be`
   - `MINIO_ACCESS_KEY=...`
   - `MINIO_SECRET_KEY=...`
5. Expose port 5000
6. Enable health check: `GET /health`
7. Deploy

### 4. Test Deployment

```bash
curl -X POST https://tod-pdf-service.your-domain.com/generate-tod \
  -H "Content-Type: application/json" \
  -d @tests/sample_input.json \
  --output deployed.pdf
```

## Integration with Logboekapp

From logboekapp, POST to this service:

```python
import requests

data = {
    "employeeName": "...",
    "date": "...",
    # ... other fields
}

response = requests.post(
    "http://tod-pdf-service:5000/generate-tod",
    json=data
)

if response.status_code == 200:
    # Save PDF
    with open("TOD.pdf", "wb") as f:
        f.write(response.content)
else:
    # Handle error
    error = response.json()
    print(f"Error: {error['error']}")
```

## Project Structure

```
tod-pdf-service/
├── app.py                  # Flask application & routes
├── pdf_generator.py        # PDF generation & overlay logic
├── validators.py           # Pydantic input models
├── config.py              # Configuration settings
├── utils.py               # MinIO & utility functions
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container build
├── docker-compose.yml     # Local dev setup
├── .env.example           # Environment template
├── .gitignore             # Git ignores
├── templates/
│   └── TOD.pdf           # Template PDF
└── tests/
    ├── test_validators.py
    ├── test_pdf_generator.py
    └── sample_input.json
```

## License

Proprietary - For internal use only

## Support

For issues or questions, contact the development team.
