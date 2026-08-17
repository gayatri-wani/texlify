import os
import io
import shutil
import logging
import tempfile
from app.core.config import settings

logger = logging.getLogger("texlify.storage")


def _get_cloudinary():
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
    return cloudinary


def upload_file(local_path: str, storage_key: str) -> str:
    """
    Upload a file to storage.
    - local_path: path to the file on disk
    - storage_key: unique identifier (e.g. 'texlify/user_1/abc123')
    Returns the storage key (Cloudinary) or local path (local dev).
    """
    if settings.use_cloudinary:
        try:
            cld = _get_cloudinary()
            result = cld.uploader.upload(
                local_path,
                public_id=storage_key,
                resource_type="raw",
                overwrite=True,
            )
            logger.info("Uploaded to Cloudinary: %s", storage_key)
            return storage_key
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e)
            raise
    else:
        # Local dev — file already on disk, just return path
        return local_path


def download_file(storage_key: str, dest_path: str):
    """
    Download a file from storage to dest_path.
    """
    if settings.use_cloudinary:
        try:
            import requests
            cld = _get_cloudinary()
            url = cld.CloudinaryImage(storage_key).build_url(
                resource_type="raw", secure=True
            )
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(response.content)
            logger.info("Downloaded from Cloudinary: %s", storage_key)
        except Exception as e:
            logger.error("Cloudinary download failed: %s", e)
            raise
    else:
        # Local dev — file already at storage_key path
        if storage_key != dest_path:
            shutil.copy2(storage_key, dest_path)


def delete_file(storage_key: str):
    """Delete a file from storage."""
    if settings.use_cloudinary:
        try:
            cld = _get_cloudinary()
            cld.uploader.destroy(storage_key, resource_type="raw")
            logger.info("Deleted from Cloudinary: %s", storage_key)
        except Exception as e:
            logger.warning("Cloudinary delete failed: %s", e)
    else:
        if os.path.exists(storage_key):
            os.remove(storage_key)


def get_temp_copy(storage_key: str, suffix: str = ".docx") -> str:
    """
    Get a local temporary copy of a file for processing.
    Always returns a local file path safe to read/write.
    Call cleanup_temp_copy() when done.
    """
    if settings.use_cloudinary:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        )
        tmp.close()
        download_file(storage_key, tmp.name)
        return tmp.name
    else:
        return storage_key


def save_temp_copy(temp_path: str, storage_key: str):
    """
    After processing a temp copy, push it back to storage.
    """
    if settings.use_cloudinary:
        upload_file(temp_path, storage_key)


def cleanup_temp_copy(temp_path: str, storage_key: str):
    """
    Delete a temporary file after use (Cloudinary mode only).
    """
    if settings.use_cloudinary and temp_path != storage_key:
        try:
            os.remove(temp_path)
        except OSError:
            pass