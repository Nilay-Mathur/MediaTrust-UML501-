from app.ml.provenance.service import provenance_service

def test_sha256_computation_and_verify():
    data = b"MediaTrust Content Integrity Test"
    # Known SHA-256 for this exact byte sequence
    digest = provenance_service.compute_sha256(data)
    assert len(digest) == 64

    # Verification match
    verify_match = provenance_service.verify_hash(data, digest)
    assert verify_match["matches"] is True
    assert verify_match["verification_status"] == "verified_match"

    # Tampered verification
    verify_tampered = provenance_service.verify_hash(b"Tampered Content", digest)
    assert verify_tampered["matches"] is False
