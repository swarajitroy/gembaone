"""Report schemas."""

from pydantic import BaseModel


class RawFileDownloadResponse(BaseModel):
    """Raw file download response."""

    download_url: str
    expires_at: str
    original_filename: str
    byte_size: int


class ReportDownloadResponse(BaseModel):
    """Report download response."""

    download_url: str
    expires_at: str
    report_type: str
    generated_at: str
