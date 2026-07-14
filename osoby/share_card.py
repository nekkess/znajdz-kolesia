import io
import textwrap

import requests
from django.conf import settings
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "Anton-Regular.ttf"

WIDTH, HEIGHT = 1080, 1080
BLACK = (10, 8, 8)
RED = (225, 6, 0)
WHITE = (255, 255, 255)
GRAY = (190, 190, 190)

PHOTO_WIDTH = 480


def _font(size):
    return ImageFont.truetype(str(FONT_PATH), size)


def _fit_font(draw, text, max_width, start_size, min_size=24):
    size = start_size
    while size > min_size:
        font = _font(size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 4
    return _font(min_size)


def _glow_text(card, xy, text, font, fill, glow_color=RED, blur=18):
    glow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text(xy, text, font=font, fill=glow_color + (255,))
    glow = glow.filter(ImageFilter.GaussianBlur(blur))
    card.alpha_composite(glow)
    ImageDraw.Draw(card).text(xy, text, font=font, fill=fill)


def _duotone_photo(photo_field):
    url = photo_field.build_url(
        width=PHOTO_WIDTH,
        height=HEIGHT,
        crop="fill",
        gravity="face",
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    photo = Image.open(io.BytesIO(response.content)).convert("L")
    photo = ImageOps.fit(photo, (PHOTO_WIDTH, HEIGHT), method=Image.LANCZOS)
    photo = ImageOps.autocontrast(photo, cutoff=1)
    duotone = ImageOps.colorize(photo, black=(15, 12, 12), white=(238, 232, 230), mid=(110, 25, 20))
    return duotone.convert("RGBA")


def _placeholder_photo():
    photo = Image.new("RGBA", (PHOTO_WIDTH, HEIGHT), (24, 19, 19, 255))
    draw = ImageDraw.Draw(photo)
    cx = PHOTO_WIDTH / 2
    cy = HEIGHT / 2
    silhouette_color = (95, 35, 32, 255)

    draw.ellipse([cx - 110, cy - 260, cx + 110, cy - 40], fill=silhouette_color)

    draw.pieslice(
        [cx - 230, cy - 40, cx + 230, cy + 420],
        180, 360,
        fill=silhouette_color,
    )
    return photo


def generate_share_card(person):
    card = Image.new("RGBA", (WIDTH, HEIGHT), BLACK + (255,))

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [WIDTH * 0.35, -260, WIDTH + 260, 480], fill=RED + (150,)
    )
    ImageDraw.Draw(glow).ellipse(
        [-260, HEIGHT - 420, WIDTH * 0.35, HEIGHT + 260], fill=RED + (90,)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    card.alpha_composite(glow)

    try:
        photo = _duotone_photo(person.photo) if person.photo else _placeholder_photo()
    except Exception:
        photo = _placeholder_photo()

    fade_mask = Image.new("L", (PHOTO_WIDTH, HEIGHT), 255)
    fade_draw = ImageDraw.Draw(fade_mask)
    fade_start = PHOTO_WIDTH - 140
    for x in range(fade_start, PHOTO_WIDTH):
        alpha = int(255 * (PHOTO_WIDTH - x) / (PHOTO_WIDTH - fade_start))
        fade_draw.line([(x, 0), (x, HEIGHT)], fill=alpha)
    card.paste(photo, (0, 0), fade_mask)

    draw = ImageDraw.Draw(card)
    text_x = PHOTO_WIDTH + 60
    max_text_width = WIDTH - text_x - 50

    draw.text((text_x, 55), "ZNAJDŹ", font=_font(42), fill=WHITE)
    draw.text((text_x, 100), "KOLESIA", font=_font(42), fill=RED)

    name_font = _fit_font(draw, f"{person.first_name} {person.last_name}".upper(), max_text_width, 84)
    y = 210
    draw.text((text_x, y), person.first_name.upper(), font=name_font, fill=WHITE)
    y += name_font.size + 6
    draw.text((text_x, y), person.last_name.upper(), font=name_font, fill=WHITE)
    y += name_font.size + 30

    role_bits = [bit for bit in (person.position, person.organization) if bit]
    role_font = _font(30)
    for line in role_bits:
        for wrapped in textwrap.wrap(line, width=28)[:2]:
            draw.text((text_x, y), wrapped, font=role_font, fill=GRAY)
            y += 38
    y += 25

    if person.current_party:
        badge_font = _font(28)
        badge_text = person.current_party.upper()
        badge_w = draw.textlength(badge_text, font=badge_font) + 40
        draw.rounded_rectangle(
            [text_x, y, text_x + badge_w, y + 52], radius=26, fill=RED
        )
        draw.text((text_x + 20, y + 10), badge_text, font=badge_font, fill=WHITE)
        y += 90

    salary_label_font = _font(26)
    draw.text((text_x, y), "WYNAGRODZENIE ROCZNE", font=salary_label_font, fill=GRAY)
    y += 45

    salary_text = person.salary_display.upper()
    salary_font = _fit_font(draw, salary_text, max_text_width, 84, min_size=44)
    _glow_text(card, (text_x, y), salary_text, salary_font, WHITE, glow_color=RED, blur=22)
    y += salary_font.size + 40

    draw = ImageDraw.Draw(card)
    draw.text((text_x, HEIGHT - 150), "ŹRÓDŁO: PUBLICZNIE DOSTĘPNE REJESTRY", font=_font(20), fill=GRAY)

    bar_h = 90
    draw.rectangle([0, HEIGHT - bar_h, WIDTH, HEIGHT], fill=RED)
    handle_font = _font(38)
    handle_text = "@ZNAJDZKOLESIA"
    handle_w = draw.textlength(handle_text, font=handle_font)
    draw.text((WIDTH - handle_w - 40, HEIGHT - bar_h + 22), handle_text, font=handle_font, fill=WHITE)

    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
