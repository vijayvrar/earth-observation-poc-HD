import math
import io
import base64
import requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# Create a global persistent HTTP session for socket reuse
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
session.mount('https://', adapter)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
}

# --- Web Mercator Tile Math ---
def lat_lon_to_tile(lat, lon, zoom=17):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

# --- Fast Tile Downloader ---
def fetch_tile(x, y, zoom=17):
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
    try:
        response = session.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching tile {x}, {y}: {e}")
    # Return dark placeholder tile if request times out or fails
    return Image.new('RGB', (256, 256), color=(15, 23, 42))

# --- High-Speed Concurrent Grid Stitcher ---
def get_stitched_satellite_image(lat, lon, zoom=17, grid_size=7):
    center_x, center_y = lat_lon_to_tile(lat, lon, zoom)
    half_grid = grid_size // 2
    
    start_x = center_x - half_grid
    start_y = center_y - half_grid
    
    tasks = []
    for row in range(grid_size):
        for col in range(grid_size):
            tx = start_x + col
            ty = start_y + row
            tasks.append((row, col, tx, ty))
            
    stitched_image = Image.new('RGB', (grid_size * 256, grid_size * 256))
    
    def process_tile(task):
        row, col, tx, ty = task
        tile_img = fetch_tile(tx, ty, zoom)
        return row, col, tile_img

    # 20 Workers + Shared Connection Pool = Sub-2-second downloads
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(process_tile, tasks)
        for row, col, tile_img in results:
            stitched_image.paste(tile_img, (col * 256, row * 256))

    buffered = io.BytesIO()
    # JPEG quality 80 speeds up Base64 encoding/decoding drastically
    stitched_image.save(buffered, format="JPEG", quality=80, optimize=True)
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return f"data:image/jpeg;base64,{img_str}"
