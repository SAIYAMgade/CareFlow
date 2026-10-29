from fastapi import Request, status
from fastapi.responses import JSONResponse
from .logging import logger

class CareFlowException(Exception):
    def __init__(self, message: str, code: str = "APPLICATION_ERROR", status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

class ResourceNotFoundException(CareFlowException):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier}
        )

class WorkflowConflictException(CareFlowException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="INVALID_STATE_TRANSITION",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class ValidationException(CareFlowException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_FAILED",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class DataIntegrityException(CareFlowException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="DATA_INTEGRITY_VIOLATION",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

async def careflow_exception_handler(request: Request, exc: CareFlowException):
    logger.warning(f"Handled error [{exc.code}]: {exc.message} on path {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please contact the system administrator.",
            "details": {}
        }
    )
