import io
from fastapi import HTTPException, UploadFile
from PIL import Image
from app.core.logging import get_logger

logger = get_logger("validation")

ALLOWED_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", 
    "image/webp", "image/bmp", "image/tiff"
}

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_FILE_SIZE = 10

def validate_image_file(file: UploadFile) -> None:
    """Validate image file"""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check extension
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {', '.join(ALLOWED_TYPES)}"
        )
    
    try:
        content = file.file.read()
        file.file.seek(0)
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(content) < MIN_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too small")
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Validate with PIL
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()
            
            image = Image.open(io.BytesIO(content))
            width, height = image.size
            
            logger.info(f"Valid: {file.filename}, {width}x{height}")
            
            if width < 10 or height < 10:
                raise HTTPException(status_code=400, detail="Image too small")
            
            if width > 10000 or height > 10000:
                raise HTTPException(status_code=400, detail="Image too large")
                
        except Exception as e:
            logger.error(f"Invalid: {file.filename}")
            raise HTTPException(status_code=400, detail="Invalid image")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {file.filename}")
        raise HTTPException(status_code=500, detail="Processing error")
    finally:
        file.file.seek(0)

def validate_pagination_params(skip: int, limit: int):
    """Validate pagination"""
    if skip < 0:
        raise HTTPException(status_code=400, detail="Skip must be >= 0")
    
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit must be > 0")
        
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be <= 1000")
    
    return skip, limit
