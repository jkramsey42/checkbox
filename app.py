from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

app = Flask(__name__)

# === CONFIGURATION ===
# Replace with your actual spreadsheet ID
SPREADSHEET_ID = "1UQtc6_iIJ5IVbdjwVgEV17MZ_0kyQ-CCc7_-LDOpL_E"
WORKSHEET_NAME = "Sheet1"  # or whatever the tab is called

# Google Sheets setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Assumes the JSON key file is in the same folder, named service_account.json
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", scope
)
gclient = gspread.authorize(creds)
sheet = gclient.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)


@app.route("/checkbox-webhook", methods=["POST"])
def checkbox_webhook():
    """
    Endpoint that Checkbox will POST to when someone completes a survey.
    """
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        # If JSON parsing fails
        return jsonify({"status": "error", "message": f"Invalid JSON: {e}"}), 400

    # --- Inspect the payload structure on first run ---
    # For debugging: print to logs so you can see what Checkbox sends
    print("Received payload:", json.dumps(data, indent=2))

    # You will need to adjust these keys based on Checkbox's actual payload.
    # For now, we guess at some common fields and fall back to "Unknown".
    # survey_name = data.get("SurveyName") or data.get("surveyName") or "UnknownSurvey"
    # response_id = data.get("ResponseId") or data.get("responseId") or "UnknownResponse"
    client_name_from_header = request.headers.get("orgname", "UnknownClient")
    numeric_id = (data.get("numeric_id") or "UnknownNumericID")

    
    # Current timestamp in a human-readable format
    timestamp = datetime.utcnow().isoformat()

    # Optional: store the whole payload as JSON string for debugging/audit
    raw_payload_str = json.dumps(data)

    # Build the row to append – order must match your sheet columns
    row = [timestamp, client_name_from_header, numeric_id, raw_payload_str]

    try:
        sheet.append_row(row, value_input_option="RAW")
    except Exception as e:
        print("Error writing to Google Sheet:", e)
        return jsonify({"status": "error", "message": "Failed to write to sheet"}), 500

    # Checkbox just needs a 200 OK or similar
    return jsonify({"status": "success"}), 200


@app.route("/", methods=["GET"])
def health_check():
    return "Checkbox webhook receiver is running.", 200


if __name__ == "__main__":
    # For local testing only; in production use gunicorn or similar
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


