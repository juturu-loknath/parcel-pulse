import io
import re
from collections import Counter
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
from app.models.schemas import OCRResponse

def _clean_phone(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    return digits if re.fullmatch(r"[6-9]\d{9}", digits) else None

def _labeled_value(text: str, labels: str, pattern: str) -> str | None:
    match = re.search(rf"(?im)(?:{labels})\s*(?:no\.?|number)?\s*[:#-]?\s*({pattern})", text)
    return match.group(1).strip() if match else None

def _place(text: str, label: str) -> str | None:
    value = _labeled_value(text, label, r"[A-Za-z][A-Za-z .()-]{2,70}")
    if not value or re.search(r"\d{4,}", value): return None
    return re.sub(r"\s+", " ", value).strip(" .:-")

def _phone_candidates(text: str) -> list[str]:
    candidates = []
    for fragment in re.findall(r"[0-9][0-9 .:-]{7,24}", text):
        phone = _clean_phone(fragment)
        if phone: candidates.append(phone)
    return candidates

def _targeted_contact_phone(image: Image.Image, region: tuple[float, float, float, float]) -> tuple[str | None, str]:
    """Read one APSRTC contact column using relative page geometry and consensus OCR."""
    width, height = image.size
    left, top, right, bottom = (int(value * dimension) for value, dimension in zip(region, (width, height, width, height)))
    crop = image.crop((left, top, right, bottom))
    enlarged = ImageOps.autocontrast(ImageOps.grayscale(crop.resize((crop.width * 5, crop.height * 5))))
    variants = (enlarged, enlarged.point(lambda pixel: 255 if pixel > 150 else 0), ImageEnhance.Contrast(enlarged).enhance(2))
    votes: Counter[str] = Counter()
    try:
        import pytesseract
        for variant in variants:
            for mode in (6, 7, 11, 12, 13):
                votes.update(_phone_candidates(pytesseract.image_to_string(variant, config=f"--psm {mode}")))
    except Exception:
        return None, "not_found"
    if not votes: return None, "not_found"
    phone, count = votes.most_common(1)[0]
    # A repeated 10-digit result inside the sender/receiver column is required. This
    # excludes support lines elsewhere on the receipt and avoids one-pass guesses.
    return (phone, "high") if count >= 2 else (None, "uncertain")

def extract_fields_from_text(text: str) -> OCRResponse:
    """Extract only values supported by APSRTC-style labels; never select bare numbers."""
    lr = _labeled_value(text, r"L\.?\s*R\.?|AWB|Consignment|Booking", r"\d[\d -]{5,20}")
    tracking_number = re.sub(r"\D", "", lr) if lr else None
    if tracking_number and not re.fullmatch(r"\d{6,16}", tracking_number): tracking_number = None
    sender_raw = _labeled_value(text, r"Sender(?:\s+mobile)?|Consignor(?:\s+mobile)?|From(?:\s+mobile)?", r"[\d ()+-]{10,22}")
    receiver_raw = _labeled_value(text, r"Receiver(?:\s+mobile)?|Consignee(?:\s+mobile)?|To(?:\s+mobile)?", r"[\d ()+-]{10,22}")
    sender_mobile, receiver_mobile = _clean_phone(sender_raw) if sender_raw else None, _clean_phone(receiver_raw) if receiver_raw else None
    booking_date = _labeled_value(text, r"Booking\s+date|Date\s+of\s+booking", r"\d{1,2}[/-][A-Za-z0-9]{2,9}[/-]\d{2,4}")
    origin, destination = _place(text, r"Origin|From\s+station"), _place(text, r"Destination|To\s+station")
    values = {"tracking_number": tracking_number, "sender_mobile": sender_mobile, "receiver_mobile": receiver_mobile, "booking_date": booking_date, "origin": origin, "destination": destination}
    confidence = {key: "high" if value else "not_found" for key, value in values.items()}
    missing = [key.replace("_", " ") for key, value in values.items() if value is None]
    note = "Review and correct the editable receipt details before tracking."
    if missing: note += " Not found: " + ", ".join(missing) + "."
    return OCRResponse(**values, field_confidence=confidence, confidence_note=note)

def extract_receipt(image_bytes: bytes) -> OCRResponse:
    try:
        image = Image.open(io.BytesIO(image_bytes)); image.verify()
    except (UnidentifiedImageError, OSError): raise ValueError("The uploaded file is not a valid image.")
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes)))
        import pytesseract
        grayscale = ImageOps.grayscale(image)
        # APSRTC receipts are sparse, columnar thermal-print layouts. A binary sparse-text
        # pass preserves separated labels and values more reliably than a single text block.
        thresholded = grayscale.point(lambda pixel: 255 if pixel > 165 else 0)
        text = pytesseract.image_to_string(thresholded, config="--psm 11")
    except Exception:
        return OCRResponse(field_confidence={}, confidence_note="OCR could not read this receipt. Please enter the details manually.")
    result = extract_fields_from_text(text)
    # APSRTC places consignor and consignee contacts in separate upper columns. The
    # regions are relative to the receipt image, not absolute camera coordinates.
    sender, sender_confidence = _targeted_contact_phone(image, (.07, .24, .48, .31))
    receiver, receiver_confidence = _targeted_contact_phone(image, (.50, .24, .78, .31))
    if sender:
        result.sender_mobile = sender
        result.field_confidence["sender_mobile"] = sender_confidence
    elif sender_confidence == "uncertain":
        result.field_confidence["sender_mobile"] = "uncertain"
    if receiver:
        result.receiver_mobile = receiver
        result.field_confidence["receiver_mobile"] = receiver_confidence
    elif receiver_confidence == "uncertain":
        result.field_confidence["receiver_mobile"] = "uncertain"
    missing = [key.replace("_", " ") for key in ("sender_mobile", "receiver_mobile") if getattr(result, key) is None]
    if missing:
        result.confidence_note = "Review the receipt details before tracking. Not found reliably: " + ", ".join(missing) + "."
    return result
