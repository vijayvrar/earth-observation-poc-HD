import base64
from io import BytesIO
import math
from PIL import Image
import requests


def latlon_to_tile(lat, lon, zoom):
    """Converts Lat/Lon coordinates to Web Mercator Tile (X, Y)."""
    lat_rad = math.radians(lat)
    n = 2.0**zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int(
        (
            1.0
            - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi
        )
        / 2.0
        * n
    )
    return xtile, ytile


def get_satellite_image(latitude, longitude):
    """Fetches Zoom 17 imagery (~1.1m/px) stitched into a 7x7 grid (1792x1792 total resolution)."""
    # Zoom 17 = ~1.1 meters per pixel (Sub-meter optical quality)
    zoom = 17
    center_x, center_y = latlon_to_tile(latitude, longitude, zoom)

    # 7x7 grid of 256x256 tiles = 1792x1792 canvas
    tile_size = 256
    grid_size = 7
    offset = grid_size // 2  # -3 to +3 range

    stitched_image = Image.new(
        "RGB", (tile_size * grid_size, tile_size * grid_size)
    )
    headers = {"User-Agent": "Mozilla/5.0"}

    # Fetch 7x7 grid asynchronously or via request loop
    for dx in range(-offset, offset + 1):
        for dy in range(-offset, offset + 1):
            x = center_x + dx
            y = center_y + dy
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"

            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                tile = Image.open(BytesIO(res.content))
                px = (dx + offset) * tile_size
                py = (dy + offset) * tile_size
                stitched_image.paste(tile, (px, py))

    # Save ultra high-resolution output
    buf = BytesIO()
    stitched_image.save(buf, format="JPEG", quality=95)
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "image": f"data:image/jpeg;base64,{image_base64}",
        "observation": "Sub-Meter High-Clarity View (Zoom 17 - 1.1m/px)",
        "latitude": latitude,
        "longitude": longitude,
    }