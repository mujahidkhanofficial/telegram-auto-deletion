"""
Replacement for the removed imghdr module in Python 3.13.
This provides minimal functionality needed by Telethon.
"""

def what(file, h=None):
    """
    Determine the type of image contained in a file or memory buffer.
    
    Args:
        file: A filename (string), a file object, or a bytes object.
        h: A bytes object containing the header of the file.
        
    Returns:
        A string describing the image type if recognized, else None.
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
            
    if h.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    elif h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'
    elif h.startswith(b'BM'):
        return 'bmp'
    elif h.startswith(b'\x00\x00\x01\x00'):
        return 'ico'
    elif h.startswith(b'\x00\x00\x02\x00'):
        return 'cur'
    elif h.startswith(b'II*\x00') or h.startswith(b'MM\x00*'):
        return 'tiff'
    return None 