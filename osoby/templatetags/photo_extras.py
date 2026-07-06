from django import template

register = template.Library()


@register.filter
def face_crop(photo, dims):
    """Crop a CloudinaryResource to "WIDTHxHEIGHT", centered on the
    detected face instead of a fixed corner - avoids cards showing just
    an eye or the top of someone's head when photos have varying framing."""

    if not photo:
        return ""

    width, height = dims.split("x")

    return photo.build_url(
        width=int(width),
        height=int(height),
        crop="fill",
        gravity="face",
    )
