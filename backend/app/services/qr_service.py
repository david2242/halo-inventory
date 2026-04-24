import io
import uuid

from sqlalchemy.orm import Session

from app.models.equipment import Equipment


def generate_qr_png(equipment: Equipment, db: Session) -> bytes:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(equipment.qr_code)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Fetch location name for label
    from app.repositories.location_repo import LocationRepository
    location = LocationRepository(db).get(equipment.location_id)
    location_name = location.name if location else ""

    label_lines = [
        equipment.name,
        location_name,
    ]
    if equipment.serial_number:
        label_lines.append(f"SN: {equipment.serial_number}")

    # Create canvas: QR + text below
    qr_w, qr_h = qr_img.size
    line_height = 18
    padding = 8
    canvas_h = qr_h + padding + len(label_lines) * line_height + padding
    canvas = Image.new("RGB", (qr_w, canvas_h), "white")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    y = qr_h + padding
    for line in label_lines:
        draw.text((4, y), line, fill="black", font=font)
        y += line_height

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()
