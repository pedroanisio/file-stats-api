import os
import logging
import mimetypes
from collections import defaultdict
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from humanize import naturalsize
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

# ---------- Logging Setup ----------
def get_logger():
    logger = logging.getLogger("file_stats_logger")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ---------- Pydantic Models ----------
class ExtensionStats(BaseModel):
    """Statistics for a specific file extension."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    count: int = Field(..., ge=1, description="Number of files with this extension")
    size: int = Field(..., ge=0, description="Total size of all files with this extension in bytes")
    
    @computed_field
    @property
    def size_human(self) -> str:
        """Human-readable size representation."""
        return naturalsize(self.size)


class FileEntry(BaseModel):
    """Detailed information about a single file."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    size: int = Field(..., ge=0, description="File size in bytes")
    path: str = Field(..., min_length=1, description="Absolute path to the file")
    name: str = Field(..., min_length=1, description="File name with extension")
    extension: str = Field(..., description="File extension (e.g., '.py', '.txt')")
    modified_time: datetime = Field(..., description="Last modification time")
    created_time: datetime = Field(..., description="File creation time")
    accessed_time: datetime = Field(..., description="Last access time")
    is_symlink: bool = Field(..., description="Whether the file is a symbolic link")
    inode: int = Field(..., ge=0, description="File inode number")
    mode: int = Field(..., ge=0, description="File mode/permissions")
    owner_uid: int = Field(..., ge=0, description="Owner user ID")
    group_gid: int = Field(..., ge=0, description="Owner group ID")
    
    @computed_field
    @property
    def size_human(self) -> str:
        """Human-readable size representation."""
        return naturalsize(self.size)
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path is absolute."""
        if not os.path.isabs(v):
            raise ValueError('Path must be absolute')
        return v


class Report(BaseModel):
    """Complete file analysis report."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    file_count: int = Field(..., ge=0, description="Total number of files analyzed")
    total_size: int = Field(..., ge=0, description="Total size of all files in bytes")
    extensions: Dict[str, ExtensionStats] = Field(..., description="Statistics grouped by file extension")
    largest_files: List[FileEntry] = Field(..., max_length=50, description="List of largest files (up to 10)")
    all_files: List[FileEntry] = Field(..., description="Complete list of all analyzed files")
    
    @computed_field
    @property
    def total_size_human(self) -> str:
        """Human-readable total size representation."""
        return naturalsize(self.total_size)
    
    @field_validator('largest_files')
    @classmethod
    def validate_largest_files(cls, v: List[FileEntry]) -> List[FileEntry]:
        """Ensure largest_files is sorted by size descending."""
        if len(v) > 1:
            for i in range(len(v) - 1):
                if v[i].size < v[i + 1].size:
                    raise ValueError('largest_files must be sorted by size in descending order')
        return v


class PaginatedFiles(BaseModel):
    """Paginated response for file listings."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    total: int = Field(..., ge=0, description="Total number of files available")
    limit: int = Field(..., ge=1, le=100, description="Maximum number of files returned")
    offset: int = Field(..., ge=0, description="Number of files skipped")
    results: List[FileEntry] = Field(..., description="Files for current page")
    
    @computed_field
    @property
    def has_next(self) -> bool:
        """Whether there are more files after this page."""
        return self.offset + self.limit < self.total
    
    @computed_field
    @property
    def has_previous(self) -> bool:
        """Whether there are files before this page."""
        return self.offset > 0


class ExtensionInfo(BaseModel):
    """Information about a single file extension."""
    extension: str = Field(..., description="File extension (e.g., '.py', '.txt')")
    count: int = Field(..., ge=1, description="Number of files with this extension")
    size: int = Field(..., ge=0, description="Total size of files with this extension in bytes")
    size_human: str = Field(..., description="Human-readable size representation")


class ExtensionListResponse(BaseModel):
    """Response containing all available extensions in a directory."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    path: str = Field(..., min_length=1, description="Directory path that was analyzed")
    total_files: int = Field(..., ge=0, description="Total number of files in the directory")
    extensions: List[ExtensionInfo] = Field(..., description="List of extensions sorted by frequency")


class FileInfoResponse(BaseModel):
    """Detailed information about a specific file with streaming URLs."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    path: str = Field(..., min_length=1, description="Absolute path to the file")
    name: str = Field(..., min_length=1, description="File name with extension")
    extension: str = Field(..., description="File extension")
    size: int = Field(..., ge=0, description="File size in bytes")
    size_human: str = Field(..., description="Human-readable size representation")
    content_type: str = Field(..., description="MIME content type")
    modified_time: str = Field(..., description="Last modification time (ISO format)")
    created_time: str = Field(..., description="File creation time (ISO format)")
    accessed_time: str = Field(..., description="Last access time (ISO format)")
    is_symlink: bool = Field(..., description="Whether the file is a symbolic link")
    inode: int = Field(..., ge=0, description="File inode number")
    mode: int = Field(..., ge=0, description="File mode/permissions")
    owner_uid: int = Field(..., ge=0, description="Owner user ID")
    group_gid: int = Field(..., ge=0, description="Owner group ID")
    stream_url: str = Field(..., description="URL to stream the file content")
    download_url: str = Field(..., description="URL to download the file")


# ---------- Logic ----------
def collect_file_stats(root_folder: str, logger: logging.Logger, extension_filter: Optional[str] = None) -> Report:
    file_count = 0
    total_size = 0
    extensions = defaultdict(lambda: {"count": 0, "size": 0})
    all_files = []

    for dirpath, _, filenames in os.walk(root_folder):
        for f in filenames:
            file_path = os.path.join(dirpath, f)
            try:
                stats = os.stat(file_path, follow_symlinks=False)
                size = stats.st_size
                
                ext = os.path.splitext(f)[1].lower()
                
                # Apply extension filter if provided
                if extension_filter and ext != extension_filter.lower():
                    continue
                
                total_size += size
                file_count += 1

                extensions[ext]["count"] += 1
                extensions[ext]["size"] += size

                file_entry = FileEntry(
                    size=size,
                    path=os.path.abspath(file_path),
                    name=f,
                    extension=ext,
                    modified_time=datetime.fromtimestamp(stats.st_mtime),
                    created_time=datetime.fromtimestamp(stats.st_ctime),
                    accessed_time=datetime.fromtimestamp(stats.st_atime),
                    is_symlink=os.path.islink(file_path),
                    inode=stats.st_ino,
                    mode=stats.st_mode,
                    owner_uid=stats.st_uid,
                    group_gid=stats.st_gid,
                )
                all_files.append(file_entry)

            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

    all_files.sort(key=lambda x: x.size, reverse=True)
    ext_stats = {
        k: ExtensionStats(count=v["count"], size=v["size"])
        for k, v in extensions.items()
    }

    filter_msg = f" (filtered by extension: {extension_filter})" if extension_filter else ""
    logger.info(f"Scanned {file_count} files{filter_msg}, total size {naturalsize(total_size)}")
    return Report(
        file_count=file_count,
        total_size=total_size,
        extensions=ext_stats,
        largest_files=all_files[:10],
        all_files=all_files,
    )


def is_safe_path(file_path: str) -> bool:
    """Check if the file path is safe (no directory traversal attacks)."""
    try:
        # Resolve the path and check if it's within allowed bounds
        resolved_path = os.path.realpath(file_path)
        return os.path.exists(resolved_path) and os.path.isfile(resolved_path)
    except (OSError, ValueError):
        return False


def generate_file_chunks(file_path: str, chunk_size: int = 8192):
    """Generate file chunks for streaming."""
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                yield chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


def get_content_type(file_path: str) -> str:
    """Get the appropriate content type for a file."""
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type or 'application/octet-stream'


# ---------- FastAPI App ----------
app = FastAPI(
    title="File Statistics API",
    description="Analyze directory file contents with metadata, extension summary, and pagination.",
    version="1.0.0",
    contact={"name": "Pedro Anisio", "email": "pedroanisio@arc4d3.com"},
)


# ---------- Routes ----------
@app.get("/", summary="Welcome")
def root():
    return JSONResponse(
        {"message": "Welcome to the File Statistics API. Use /docs or /redoc for API reference."}
    )


@app.get("/analyze", response_model=Report, summary="Full analysis of all files")
def analyze_directory(
    path: str, 
    extension: Optional[str] = Query(None, description="Filter by file extension (e.g., '.py', '.txt')"),
    logger: logging.Logger = Depends(get_logger)
):
    if not os.path.isdir(path):
        logger.error(f"Invalid path requested: {path}")
        raise HTTPException(status_code=400, detail="Invalid directory path")
    logger.info(f"Analyzing directory: {path}")
    return collect_file_stats(path, logger, extension)


@app.get("/analyze/extensions", response_model=ExtensionListResponse, summary="Get all available extensions in directory")
def get_available_extensions(
    path: str,
    logger: logging.Logger = Depends(get_logger)
):
    """Get a list of all file extensions available in the specified directory."""
    if not os.path.isdir(path):
        logger.error(f"Invalid path for extensions: {path}")
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    logger.info(f"Getting available extensions in: {path}")
    report = collect_file_stats(path, logger)
    
    # Sort extensions by count (most common first)
    sorted_extensions = sorted(
        report.extensions.items(), 
        key=lambda x: x[1].count, 
        reverse=True
    )
    
    extensions_info = [
        ExtensionInfo(
            extension=ext,
            count=stats.count,
            size=stats.size,
            size_human=naturalsize(stats.size)
        )
        for ext, stats in sorted_extensions
    ]
    
    return ExtensionListResponse(
        path=path,
        total_files=report.file_count,
        extensions=extensions_info
    )


@app.get("/stream", summary="Stream file contents")
def stream_file(
    file_path: str = Query(..., description="Full path to the file to stream"),
    download: bool = Query(False, description="Force download instead of inline display"),
    logger: logging.Logger = Depends(get_logger)
):
    """Stream file contents with appropriate content type detection."""
    
    # Security check
    if not is_safe_path(file_path):
        logger.error(f"Invalid or unsafe file path requested: {file_path}")
        raise HTTPException(status_code=400, detail="Invalid file path or file does not exist")
    
    try:
        # Get file info
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        filename = os.path.basename(file_path)
        content_type = get_content_type(file_path)
        
        logger.info(f"Streaming file: {file_path} ({naturalsize(file_size)})")
        
        # Prepare headers
        headers = {
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        }
        
        # Set content disposition
        disposition = "attachment" if download else "inline"
        headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        
        # Create streaming response
        return StreamingResponse(
            generate_file_chunks(file_path),
            media_type=content_type,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error streaming file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error streaming file: {str(e)}")


@app.get("/file-info", response_model=FileInfoResponse, summary="Get file information without streaming content")
def get_file_info(
    file_path: str = Query(..., description="Full path to the file"),
    logger: logging.Logger = Depends(get_logger)
):
    """Get detailed information about a specific file without streaming its content."""
    
    # Security check
    if not is_safe_path(file_path):
        logger.error(f"Invalid or unsafe file path requested: {file_path}")
        raise HTTPException(status_code=400, detail="Invalid file path or file does not exist")
    
    try:
        stats = os.stat(file_path, follow_symlinks=False)
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        content_type = get_content_type(file_path)
        
        logger.info(f"Getting info for file: {file_path}")
        
        return FileInfoResponse(
            path=os.path.abspath(file_path),
            name=filename,
            extension=ext,
            size=stats.st_size,
            size_human=naturalsize(stats.st_size),
            content_type=content_type,
            modified_time=datetime.fromtimestamp(stats.st_mtime).isoformat(),
            created_time=datetime.fromtimestamp(stats.st_ctime).isoformat(),
            accessed_time=datetime.fromtimestamp(stats.st_atime).isoformat(),
            is_symlink=os.path.islink(file_path),
            inode=stats.st_ino,
            mode=stats.st_mode,
            owner_uid=stats.st_uid,
            group_gid=stats.st_gid,
            stream_url=f"/stream?file_path={file_path}",
            download_url=f"/stream?file_path={file_path}&download=true"
        )
        
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")


@app.get("/analyze/files", response_model=PaginatedFiles, summary="Paginated file list")
def get_paginated_files(
    path: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    extension: Optional[str] = Query(None, description="Filter by file extension (e.g., '.py', '.txt')"),
    logger: logging.Logger = Depends(get_logger),
):
    if not os.path.isdir(path):
        logger.error(f"Invalid path for pagination: {path}")
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    logger.info(f"Paginating files in: {path}, offset={offset}, limit={limit}")
    report = collect_file_stats(path, logger, extension)
    total = len(report.all_files)
    results = report.all_files[offset:offset + limit]
    return PaginatedFiles(total=total, limit=limit, offset=offset, results=results)
