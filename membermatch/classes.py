# classes.py
from .settings import DEFAULT_STATUS_CODE, DEFAULT_CODE, DEFAULT_SEVERITY, DEFAULT_DESCRIPTION
from werkzeug.exceptions import HTTPException

class OperationOutcomeException(HTTPException):
    '''
    handle errors with an Operation Outcome
    '''

    def __init__(self, status_code=None, code=None, severity=None, description=None):
        if status_code is not None:
            self.status_code = status_code
        else:
            self.status_code = DEFAULT_STATUS_CODE
        if code is not None:
            self.code = code
        else:
            self.code = DEFAULT_CODE
        if severity is not None:
            self.severity = severity
        else:
            self.severity = DEFAULT_SEVERITY
        if description is not None:
            self.description = description
        else:
            self.description = DEFAULT_DESCRIPTION
        super().__init__()
