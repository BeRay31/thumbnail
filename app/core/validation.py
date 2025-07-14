import io
from typing import Set
from fastapi import HTTPException, UploadFile
from PIL import Image
from app.core.logging import get_logger

logger = get_logger("validation")

# Allowed image MIME types
ALLOWED_IMAGE_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff"
}

# Allowed file extensions
ALLOWED_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"
}

# File size limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_FILE_SIZE = 100  # 100 bytes

def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file
    
    Args:
        file: The uploaded file
        
    Raises:
        HTTPException: If validation fails
    """
    # Check if file is provided
    if not file or not file.filename:
        logger.warning("No file provided in upload")
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        logger.warning(f"Invalid file extension for file: {file.filename}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        logger.warning(f"Invalid content type: {file.content_type} for file: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read file content for further validation
    try:
        content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(content)} bytes for file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(content) < MIN_FILE_SIZE:
            logger.warning(f"File too small: {len(content)} bytes for file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"File too small. Minimum size: {MIN_FILE_SIZE} bytes"
            )
        
        # Validate that it's actually an image by opening with PIL
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()  # Verify it's a valid image
            
            # Reset and get basic image info
            image = Image.open(io.BytesIO(content))
            width, height = image.size
            
            logger.info(f"Valid image uploaded: {file.filename}, size: {width}x{height}, format: {image.format}")
            
            # Check minimum dimensions
            if width < 10 or height < 10:
                raise HTTPException(
                    status_code=400,
                    detail="Image dimensions too small (minimum 10x10 pixels)"
                )
            
            # Check maximum dimensions  
            if width > 10000 or height > 10000:
                raise HTTPException(
                    status_code=400,
                    detail="Image dimensions too large (maximum 10000x10000 pixels)"
                )
                
        except Exception as e:
            logger.error(f"Invalid image file: {file.filename}, error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid image file or corrupted image data"
            )
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error validating file: {file.filename}, error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing uploaded file")

def validate_pagination_params(skip: int, limit: int) -> tuple[int, int]:
    """
    Validate and sanitize pagination parameters
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Tuple of validated (skip, limit)
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if skip < 0:
        raise HTTPException(status_code=400, detail="Skip parameter must be >= 0")
    
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit parameter must be > 0")
        
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit parameter must be <= 1000")
    
    return skip, limit
