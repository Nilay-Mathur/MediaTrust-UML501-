from app.security.file_validator import validate_image_file, validate_video_file, sanitize_filename

def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd.jpg") == "passwd.jpg"
    assert sanitize_filename("my test file!@#.png") == "my_test_file___.png"

def test_validate_image_file_signatures():
    # Valid JPEG
    jpeg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
    valid, _, mime = validate_image_file(jpeg_bytes, "test.jpg")
    assert valid is True
    assert mime == "image/jpeg"

    # Valid PNG
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    valid, _, mime = validate_image_file(png_bytes, "test.png")
    assert valid is True
    assert mime == "image/png"

    # Invalid executable disguised as image
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    valid, err, _ = validate_image_file(exe_bytes, "exploit.jpg")
    assert valid is False
    assert "File signature does not match" in err
