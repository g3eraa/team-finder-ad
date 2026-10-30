import random
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

AVATAR_SIZE = 256
FONT_PATH = (
    settings.BASE_DIR / "static" / "fonts" / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
)
TEXT_COLOR = "#FFFFFF"
BACKGROUND_COLORS = (
    "#5B7DB1",
    "#5F8D4E",
    "#9A6FA8",
    "#C0674A",
    "#3F8E8C",
    "#8B6F47",
    "#7466A8",
    "#B5577A",
)


def _load_font(size):
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.load_default(size)


def generate_avatar(name):
    letter = ((name or "").strip()[:1] or "?").upper()
    background = random.choice(BACKGROUND_COLORS)
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), background)
    ImageDraw.Draw(image).text(
        (AVATAR_SIZE / 2, AVATAR_SIZE / 2),
        letter,
        fill=TEXT_COLOR,
        font=_load_font(AVATAR_SIZE // 2),
        anchor="mm",
    )
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"avatar_{uuid.uuid4()}.png")
