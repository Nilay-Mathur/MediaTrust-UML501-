import hashlib
import io
from typing import Dict, Any, Optional
from PIL import Image, ExifTags
from app.core.logging import logger

AI_GENERATION_SIGNATURES = [
    "stable diffusion", "midjourney", "dall-e", "novelai", "comfyui", 
    "automatic1111", "adobe firefly", "bing image creator", "flux"
]

class ProvenanceService:
    def compute_sha256(self, file_bytes: bytes) -> str:
        """Computes cryptographic SHA-256 digest of input bytes."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    def verify_hash(self, file_bytes: bytes, claimed_hash: str) -> Dict[str, Any]:
        actual_hash = self.compute_sha256(file_bytes)
        matches = actual_hash.lower() == claimed_hash.lower().strip()

        return {
            "actual_sha256": actual_hash,
            "claimed_sha256": claimed_hash,
            "matches": matches,
            "verification_status": "verified_match" if matches else "integrity_tampered_or_mismatch",
            "scope_note": "SHA-256 verifies bit-for-bit file integrity against the claimed hash; it does not verify whether the original content is authentic."
        }

    def inspect_image_provenance(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Inspects EXIF metadata, camera hardware tags, and generative AI signatures.
        """
        sha256_hash = self.compute_sha256(image_bytes)
        metadata_found = {}
        ai_signatures_found = []
        has_camera_hardware_tags = False

        try:
            img = Image.open(io.BytesIO(image_bytes))
            exif_data = img.getexif()

            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    # Convert bytes to string safely
                    val_str = str(value).strip() if value is not None else ""
                    if val_str:
                        metadata_found[tag_name] = val_str[:150]  # bounded string length

                        # Check for AI signatures in software/make/model
                        low_val = val_str.lower()
                        for sig in AI_GENERATION_SIGNATURES:
                            if sig in low_val:
                                ai_signatures_found.append(f"{tag_name}: {val_str}")

                        if tag_name in ("Make", "Model", "FocalLength", "ExposureTime", "FNumber", "ISOSpeedRatings"):
                            has_camera_hardware_tags = True
        except Exception as e:
            logger.warning(f"EXIF parsing error: {str(e)}")

        has_exif = len(metadata_found) > 0
        software = metadata_found.get("Software", "None")

        return {
            "content_sha256": sha256_hash,
            "has_exif_metadata": has_exif,
            "has_camera_hardware_tags": has_camera_hardware_tags,
            "software_tool": software,
            "detected_ai_signatures": ai_signatures_found,
            "metadata_summary": metadata_found,
            "provenance_verdict": "synthetic_provenance_detected" if ai_signatures_found else (
                "camera_metadata_present" if has_camera_hardware_tags else "metadata_stripped_or_absent"
            ),
            "methodology_note": "Missing EXIF metadata is common on social media platforms (which strip EXIF for privacy) and does not inherently prove manipulation."
        }

provenance_service = ProvenanceService()
