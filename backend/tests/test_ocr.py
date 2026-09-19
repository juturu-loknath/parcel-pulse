import io
from PIL import Image
import pytesseract
from app.services.ocr import _targeted_contact_phone, extract_fields_from_text, extract_receipt

def test_extracts_labeled_apsrtc_fields_without_using_helpline_numbers():
    receipt = """APSRTC LOGISTICS
    Helpline: 1800 425 1111
    LR No: 12345678
    Sender Mobile: 9123456789
    Receiver Mobile: 9876543210
    Booking Date: 18-09-2026
    Origin: Hyderabad MGBS
    Destination: Pulivendula
    GSTIN: 36ABCDE1234F1Z5
    """
    result = extract_fields_from_text(receipt)
    assert result.tracking_number == "12345678"
    assert result.sender_mobile == "9123456789"
    assert result.receiver_mobile == "9876543210"
    assert result.booking_date == "18-09-2026"
    assert result.origin == "Hyderabad MGBS"
    assert result.destination == "Pulivendula"
    assert result.field_confidence["receiver_mobile"] == "high"

def test_marks_unlabeled_or_missing_values_as_not_found():
    result = extract_fields_from_text("Helpline 1800 425 1111\nValue 9999\n")
    assert result.tracking_number is None
    assert result.sender_mobile is None
    assert result.receiver_mobile is None
    assert result.field_confidence["tracking_number"] == "not_found"

def test_rejects_non_image():
    try: extract_receipt(b"not an image")
    except ValueError as exc: assert "valid image" in str(exc)
    else: raise AssertionError("invalid upload accepted")

def test_returns_manual_entry_message_when_tesseract_fails(monkeypatch):
    image = Image.new("RGB", (20, 20), "white")
    data = io.BytesIO(); image.save(data, "PNG")
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("OCR unavailable")))
    result = extract_receipt(data.getvalue())
    assert result.tracking_number is None
    assert "manually" in result.confidence_note

def test_targeted_contact_ocr_requires_consensus_for_a_fictional_customer_number(monkeypatch):
    image = Image.new("RGB", (1000, 1200), "white")
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *args, **kwargs: "Consignor No: 9123456789")
    phone, confidence = _targeted_contact_phone(image, (.07, .24, .48, .31))
    assert phone == "9123456789"
    assert confidence == "high"

def test_targeted_contact_ocr_does_not_accept_a_one_pass_number(monkeypatch):
    calls = iter(["Consignee No: 9876543210", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    image = Image.new("RGB", (1000, 1200), "white")
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *args, **kwargs: next(calls))
    phone, confidence = _targeted_contact_phone(image, (.50, .24, .78, .31))
    assert phone is None
    assert confidence == "uncertain"
