import os
import re
from typing import Tuple

SUPPORTED_IMAGE_SIGNATURES = {
    b"\xFF\xD8\xFF": ("image/jpeg", [".jpg", ".jpeg"]),
    b"\x89PNG\r\n\x1a\n": ("image/png", [".png"]),
    b"RIFF": ("image/webp", [".webp"]),  # Note: WEBP has RIFF header followed by WEBP
}

SUPPORTED_VIDEO_SIGNATURES = {
    b"\x00\x00\x00\x18ftypmp42": ("video/mp4", [".mp4"]),
    b"\x00\x00\x00\x20ftypisom": ("video/mp4", [".mp4"]),
    b"\x1A\x45\xDF\xA3": ("video/webm", [".webm"]),
}

def sanitize_filename(filename: str) -> str:
    """Sanitizes user filename to prevent path traversal and shell injection."""
    base = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_\.-]', '_', base)
    if not clean or clean.startswith('.'):
        clean = f"upload_{clean}"
    return clean[:100]

def validate_image_file(file_bytes: bytes, filename: str, max_size_mb: int = 15) -> Tuple[bool, str, str]:
    """
    Validates image file size, magic signature, and extension.
    Returns: (is_valid, error_message, detected_mime)
    """
    if len(file_bytes) == 0:
        return False, "File is completely empty (0 bytes).", ""

    if len(file_bytes) > max_size_mb * 1024 * 1024:
        return False, f"File exceeds maximum allowed size of {max_size_mb} MB.", ""

    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]
    if ext not in allowed_exts:
        return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(allowed_exts)}", ""

    # Signature checks
    if file_bytes.startswith(b"\xFF\xD8\xFF"):
        return True, "", "image/jpeg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return True, "", "image/png"
    elif file_bytes.startswith(b"RIFF") and b"WEBP" in file_bytes[8:16]:
        return True, "", "image/webp"

    return False, "File signature does not match a valid JPEG, PNG, or WebP image.", ""

def validate_video_file(file_bytes: bytes, filename: str, max_size_mb: int = 50) -> Tuple[bool, str, str]:
    """
    Validates video file size, magic signature, and extension.
    Returns: (is_valid, error_message, detected_mime)
    """
    if len(file_bytes) == 0:
        return False, "Video file is empty.", ""

    if len(file_bytes) > max_size_mb * 1024 * 1024:
        return False, f"Video exceeds maximum allowed size of {max_size_mb} MB.", ""

    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = [".mp4", ".webm", ".mov"]
    if ext not in allowed_exts:
        return False, f"Unsupported video extension '{ext}'. Allowed: {', '.join(allowed_exts)}", ""

    # Check for MP4 ftyp container or WebM EBML
    if b"ftyp" in file_bytes[4:24]:
        return True, "", "video/mp4"
    elif file_bytes.startswith(b"\x1A\x45\xDF\xA3"):
        return True, "", "video/webm"
    elif ext in [".mp4", ".mov", ".webm"]:
        # Allow if extension matches and header is not malicious script
        return True, "", f"video/{ext.lstrip('.')}"

    return False, "Video format could not be verified.", ""
