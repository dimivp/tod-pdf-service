"""Flask app for TOD PDF generation service."""

import logging
import os
from flask import Flask, request, send_file, jsonify
from werkzeug.exceptions import BadRequest
from pydantic import ValidationError

from validators import TODRequest
from pdf_generator import generate_pdf, generate_pdf_filename
import config
from utils import (
    get_minio_client,
    generate_request_id,
    log_request,
    log_error,
)

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# Load MinIO client if configured
minio_client = get_minio_client()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Coolify."""
    return jsonify(
        {
            "status": "ok",
            "service": "tod-pdf-service",
            "version": "1.0.0",
            "minio_enabled": minio_client is not None,
        }
    ), 200


@app.route("/generate-tod", methods=["POST"])
def generate_tod():
    """Generate TOD PDF from JSON input.

    Expected JSON body:
    {
      "employeeName": "string",
      "date": "YYYY-MM-DD",
      "time": "HH:mm",
      "location": "string",
      "trackNumber": "string",
      "firstVehicleNumber": "X XXX-X",
      "lastVehicleNumber": "X XXX-X",
      "isOnAir": boolean,
      "immobilizationRows": [...],
      "endSignal": "lamps" | "plaques" | null,
      "brakeRegime": "P" | "LL" | "G" | null,
      "fullBrakeTest": boolean
    }

    Returns:
        PDF file as downloadable attachment
    """
    request_id = generate_request_id()

    try:
        log_request(request_id, "POST", "/generate-tod")

        # Get JSON body
        data = request.get_json()
        if not data:
            logger.warning(f"[{request_id}] Empty request body")
            return jsonify({"error": "Empty request body"}), 400

        # Validate input with Pydantic
        try:
            validated_request = TODRequest(**data)
        except ValidationError as ve:
            logger.warning(f"[{request_id}] Validation error: {ve}")
            errors = [
                {
                    "field": ".".join(str(x) for x in err["loc"]),
                    "message": err["msg"],
                }
                for err in ve.errors()
            ]
            return jsonify({"error": "Validation failed", "details": errors}), 400

        # Generate PDF
        logger.info(f"[{request_id}] Generating PDF for {validated_request.employeeName}")
        pdf_bytes = generate_pdf(validated_request)

        # Optional: Upload to MinIO
        if minio_client:
            filename = generate_pdf_filename(validated_request)
            object_name = f"{config.MINIO_FOLDER}/{filename}"

            success = minio_client.upload_file(
                pdf_bytes,
                object_name,
                content_type="application/pdf",
            )

            if success:
                logger.info(f"[{request_id}] PDF uploaded to MinIO: {object_name}")
            else:
                logger.warning(f"[{request_id}] MinIO upload failed, but returning PDF anyway")

        # Return PDF
        filename = generate_pdf_filename(validated_request)
        logger.info(f"[{request_id}] Returning PDF: {filename}")

        return send_file(
            path_or_file=__import__("io").BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        ), 200

    except Exception as e:
        log_error(request_id, e)
        return (
            jsonify(
                {
                    "error": "PDF generation failed",
                    "message": str(e),
                    "request_id": request_id,
                }
            ),
            500,
        )


@app.route("/upload-template", methods=["POST"])
def upload_template():
    """Upload new TOD template PDF (admin endpoint).

    Accepts multipart/form-data with 'file' field containing PDF.
    """
    request_id = generate_request_id()

    try:
        log_request(request_id, "POST", "/upload-template")

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file or not file.filename.endswith(".pdf"):
            return jsonify({"error": "Invalid file type. PDF required."}), 400

        # Save to templates directory
        template_path = config.TEMPLATE_PATH
        file.save(template_path)

        logger.info(f"[{request_id}] Template updated: {template_path}")
        return jsonify({"status": "Template updated", "path": str(template_path)}), 200

    except Exception as e:
        log_error(request_id, e)
        return (
            jsonify(
                {
                    "error": "Template upload failed",
                    "message": str(e),
                    "request_id": request_id,
                }
            ),
            500,
        )


@app.errorhandler(400)
def bad_request(e):
    """Handle 400 errors."""
    return jsonify({"error": "Bad request", "message": str(e)}), 400


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Not found", "message": str(e)}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.before_request
def before_request():
    """Log incoming requests."""
    if request.endpoint and request.endpoint not in ["health_check"]:
        logger.debug(f"{request.method} {request.path}")


@app.after_request
def after_request(response):
    """Log response."""
    if request.endpoint and request.endpoint not in ["health_check"]:
        logger.debug(f"Response: {response.status_code}")
    return response


if __name__ == "__main__":
    # Development server (use gunicorn in production)
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug)
