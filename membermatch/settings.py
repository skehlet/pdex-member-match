# settings.py
# Global settings

DEFAULT_DESCRIPTION = "unprocessable entity"
DEFAULT_STATUS_CODE = 422
DEFAULT_SEVERITY = "error"
DEFAULT_CODE = "processing"
REQUIRED_PARAMETERS = ["MemberPatient", "CoverageToMatch", "Consent"]
DEFAULT_PORT = 8000

FHIR_BASE_URL = "http://localhost:8080/fhir"
FHIR_BASE_URI = FHIR_BASE_URL

SECURE_URL = False   # True
TENANT = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
AUTH_URL = ""

# Values = "EXCLUDED" | "INCLUDED_LABELLED" | "INCLUDED_NOLABEL"
FHIR_STORE_SENSITIVITY = "EXCLUDED"

