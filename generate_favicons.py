import os
import math
from PIL import Image, ImageDraw

def create_favicon():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    icons_dir = os.path.join(static_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)

    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Rounded Rectangle (Squircle) with Gradient
    # Gradient colors: top-left #10B981 (16, 185, 129), bottom-right #047857 (4, 120, 87)
    radius = 240
    # Draw base mask
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    margin = 48
    mask_draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, fill=255)

    # Create gradient background
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    for y in range(size):
        ratio = y / size
        # Subtle angle effect with y
        r = int(16 * (1 - ratio) + 4 * ratio)
        g = int(185 * (1 - ratio) + 120 * ratio)
        b = int(129 * (1 - ratio) + 87 * ratio)
        grad_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Apply mask to gradient
    img.paste(grad, (0, 0), mask)

    # Re-draw for vector shapes with alpha
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    # Subtle inner border / highlight at top
    ov_draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, outline=(255, 255, 255, 45), width=12)

    # 2. Draw Sprout Elements
    # Main curved stem
    stem_points = [
        (512, 790),
        (512, 680),
        (510, 560),
        (525, 430),
        (555, 330)
    ]
    # Draw thick stem with rounded joints
    for i in range(len(stem_points) - 1):
        p1 = stem_points[i]
        p2 = stem_points[i + 1]
        t = i / len(stem_points)
        w = int(58 * (1 - t * 0.45))
        ov_draw.line([p1, p2], fill=(255, 255, 255, 250), width=w)
    
    # Cap the stem bottom
    ov_draw.ellipse([483, 760, 541, 818], fill=(255, 255, 255, 250))

    # Left Leaf: curved organic shape
    # Defined via a smooth closed polygon
    left_leaf = []
    # Base at stem: (510, 600)
    # Tip at: (265, 450)
    steps = 40
    # Upper curve from base to tip
    for s in range(steps + 1):
        u = s / steps
        # Bezier: P0=(510, 580), P1=(350, 400), P2=(265, 450)
        bx = (1-u)**2 * 510 + 2*(1-u)*u * 340 + u**2 * 265
        by = (1-u)**2 * 580 + 2*(1-u)*u * 390 + u**2 * 450
        left_leaf.append((bx, by))
    # Lower curve from tip back to base
    for s in range(steps + 1):
        u = s / steps
        # Bezier: P0=(265, 450), P1=(330, 620), P2=(510, 640)
        bx = (1-u)**2 * 265 + 2*(1-u)*u * 350 + u**2 * 510
        by = (1-u)**2 * 450 + 2*(1-u)*u * 640 + u**2 * 640
        left_leaf.append((bx, by))

    ov_draw.polygon(left_leaf, fill=(240, 253, 244, 255))
    
    # Left leaf subtle central vein
    left_vein = []
    for s in range(25):
        u = s / 24
        vx = (1-u) * 490 + u * 295
        vy = (1-u) * 605 + u * 465
        left_vein.append((vx, vy))
    for i in range(len(left_vein) - 1):
        ov_draw.line([left_vein[i], left_vein[i+1]], fill=(16, 185, 129, 140), width=10)

    # Right Leaf: soaring upwards and right
    right_leaf = []
    # Base at stem: (525, 470)
    # Tip at: (765, 305)
    for s in range(steps + 1):
        u = s / steps
        # Upper curve: P0=(525, 470), P1=(590, 240), P2=(765, 305)
        bx = (1-u)**2 * 525 + 2*(1-u)*u * 590 + u**2 * 765
        by = (1-u)**2 * 470 + 2*(1-u)*u * 230 + u**2 * 305
        right_leaf.append((bx, by))
    for s in range(steps + 1):
        u = s / steps
        # Lower curve: P0=(765, 305), P1=(720, 480), P2=(545, 520)
        bx = (1-u)**2 * 765 + 2*(1-u)*u * 710 + u**2 * 545
        by = (1-u)**2 * 305 + 2*(1-u)*u * 490 + u**2 * 520
        right_leaf.append((bx, by))

    ov_draw.polygon(right_leaf, fill=(255, 255, 255, 255))

    # Right leaf subtle central vein
    right_vein = []
    for s in range(25):
        u = s / 24
        vx = (1-u) * 545 + u * 735
        vy = (1-u) * 480 + u * 325
        right_vein.append((vx, vy))
    for i in range(len(right_vein) - 1):
        ov_draw.line([right_vein[i], right_vein[i+1]], fill=(16, 185, 129, 140), width=10)

    # Golden soil accent mound at base
    ov_draw.arc([390, 770, 634, 850], start=0, end=180, fill=(251, 191, 36, 220), width=14)

    # Composite overlay on background
    final_img = Image.alpha_composite(img, overlay)

    # Export various resolutions
    sizes = {
        "icon-512.png": (512, 512),
        "icon-192.png": (192, 192),
        "apple-touch-icon.png": (180, 180),
        "favicon-32x32.png": (32, 32),
        "favicon-16x16.png": (16, 16)
    }

    # Save PWA icons
    final_img.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(icons_dir, "icon-512.png"))
    final_img.resize((192, 192), Image.Resampling.LANCZOS).save(os.path.join(icons_dir, "icon-192.png"))

    # Save in static/
    final_img.resize((180, 180), Image.Resampling.LANCZOS).save(os.path.join(static_dir, "apple-touch-icon.png"))
    img_32 = final_img.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save(os.path.join(static_dir, "favicon-32x32.png"))
    img_16 = final_img.resize((16, 16), Image.Resampling.LANCZOS)
    img_16.save(os.path.join(static_dir, "favicon-16x16.png"))

    # Save multi-size favicon.ico
    img_48 = final_img.resize((48, 48), Image.Resampling.LANCZOS)
    ico_path = os.path.join(static_dir, "favicon.ico")
    img_48.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    print(f"Generated all icons successfully! Favicon at: {ico_path}")

if __name__ == "__main__":
    create_favicon()
