import os
from PIL import Image, ImageDraw, ImageFilter

def generate_logo_icon():
    # Create a 256x256 image with transparent background
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Coordinates for drop shadow
    # Draw soft shadow at bottom
    draw.ellipse([30, 220, 226, 245], fill=(0, 0, 0, 80))
    
    # Draw gold 3D thickness (extrusion) by layering ellipses
    for i in range(10):
        offset = 190 + i
        draw.ellipse([20, 20 + i, 236, offset + i], fill=(140, 88, 25, 255))
        
    # Draw primary gold face
    # Draw a gold circle
    draw.ellipse([20, 20, 236, 236], fill=(232, 168, 56, 255))
    
    # Draw radial-like shine effect (inner circle highlight)
    draw.ellipse([25, 25, 231, 231], outline=(245, 200, 66, 255), width=6)
    
    # Draw eyes (classic black eyes with pupil highlights)
    # Left eye
    draw.ellipse([80, 100, 110, 130], fill=(15, 15, 20, 255))
    draw.ellipse([98, 104, 106, 112], fill=(255, 255, 255, 255)) # highlight
    
    # Right eye
    draw.ellipse([146, 100, 176, 130], fill=(15, 15, 20, 255))
    draw.ellipse([164, 104, 172, 112], fill=(255, 255, 255, 255)) # highlight
    
    # Cheerful curved mouth
    # Draw an arc for the smile
    draw.arc([105, 125, 151, 155], start=0, end=180, fill=(15, 15, 20, 255), width=5)
    
    # Sparkle star in top-right
    # Draw a small gold star or diamond highlight
    draw.polygon([(190, 50), (195, 60), (205, 65), (195, 70), (190, 80), (185, 70), (175, 65), (185, 60)], fill=(255, 255, 255, 255))

    # Save as ICO with multiple standard Windows sizes
    icon_path = "c:/Users/aasis/OneDrive - Vignan University/Desktop/Agentic AI Project/icon.ico"
    img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"✅ Icon successfully generated at {icon_path}")

if __name__ == "__main__":
    generate_logo_icon()
