import ctypes
from ctypes import windll
from PIL import Image

def screenshot_win32(bbox):
    """Take screenshot using Windows GDI32 API"""
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    
    # Get device contexts
    hdesktop = windll.user32.GetDesktopWindow()
    desktop_dc = windll.user32.GetWindowDC(hdesktop)
    img_dc = windll.gdi32.CreateCompatibleDC(desktop_dc)
    
    # Create bitmap
    bitmap = windll.gdi32.CreateCompatibleBitmap(desktop_dc, width, height)
    windll.gdi32.SelectObject(img_dc, bitmap)
    
    # Copy screen to bitmap
    windll.gdi32.BitBlt(img_dc, 0, 0, width, height, desktop_dc, left, top, 0x00CC0020)  # SRCCOPY
    
    # Get bitmap data
    bmpinfo = ctypes.create_string_buffer(40)  # BITMAPINFOHEADER
    ctypes.memset(bmpinfo, 0, 40)
    ctypes.c_long.from_buffer(bmpinfo, 0).value = 40  # biSize
    ctypes.c_long.from_buffer(bmpinfo, 4).value = width  # biWidth
    ctypes.c_long.from_buffer(bmpinfo, 8).value = -height  # biHeight (negative for top-down)
    ctypes.c_short.from_buffer(bmpinfo, 12).value = 1  # biPlanes
    ctypes.c_short.from_buffer(bmpinfo, 14).value = 32  # biBitCount
    
    # Create buffer for pixel data
    buffer_size = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_size)
    
    # Get bitmap bits
    windll.gdi32.GetDIBits(img_dc, bitmap, 0, height, buffer, bmpinfo, 0)  # DIB_RGB_COLORS
    
    # Cleanup
    windll.gdi32.DeleteObject(bitmap)
    windll.gdi32.DeleteDC(img_dc)
    windll.user32.ReleaseDC(hdesktop, desktop_dc)
    
    # Convert to PIL Image
    img = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)
    return img.convert('RGB')

# Test on secondary monitor
bbox = (3432, -8, 5368, 1040)
print(f'Testing Win32 GDI32: {bbox}')
screenshot = screenshot_win32(bbox)
screenshot.save('test_win32_gdi32.png')
print(f'Saved: {screenshot.size}')
print(f'File size: {len(open("test_win32_gdi32.png", "rb").read())} bytes')
