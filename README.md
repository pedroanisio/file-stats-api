# 📊 File Stats API

**A FastAPI-based service for analyzing and reporting metadata from files in a directory.**  
It provides detailed information such as file sizes, extensions, timestamps, ownership, and more — with pagination and extension statistics included.

## 🔧 **API Enhancements**

| Feature              | Status | Implementation                                    |
| -------------------- | ------ | ------------------------------------------------- |
| ✅ **Pagination**     | ✅ Done | Query params: `limit`, `offset` on `/analyze/files` |
| ✅ **ReDoc**          | ✅ Done | Built-in at `/redoc`                              |
| ✅ **OpenAPI docs**   | ✅ Done | Available at `/docs`                              |
| ✅ **OpenAPI metadata** | ✅ Done | Title, description, version, contact info       |

---

## 🚀 Features

- Full directory scan and file metadata extraction
- Extension-based statistics (count and size)
- Largest files highlight
- **✅ Pagination support** with configurable limit/offset
- **✅ Full OpenAPI/Swagger documentation** at `/docs`
- **✅ ReDoc documentation** at `/redoc`
- **✅ Complete API metadata** with title, description, version
- Human-readable sizes via `humanize`
- Built-in logging with structured output
- Detailed file metadata (timestamps, ownership, inodes)

---

## 🧠 Technologies Used

- [FastAPI](https://fastapi.tiangolo.com/) for the API
- [Pydantic](https://docs.pydantic.dev/) for data models and validation
- [humanize](https://github.com/jmoiron/humanize) for readable size outputs
- Python Standard Library modules: `os`, `datetime`, `collections`, `logging`

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/file-stats-api.git
cd file-stats-api
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 🛠️ API Endpoints

### `GET /`
Basic welcome message.

### `GET /analyze?path=<directory_path>`
Performs a full scan of the directory and returns:
* Total file count
* Total size  
* Summary by file extension
* Top 10 largest files
* Full list of files and metadata

### `GET /analyze/files?path=<path>&limit=10&offset=0`
**✅ Paginated** file list with detailed metadata including:
* Query parameters: `limit` (1-100, default: 10), `offset` (≥0, default: 0)
* Returns: total count, pagination info, and file results

### `GET /docs`
**✅ Interactive Swagger UI** for testing the API

### `GET /redoc`
**✅ ReDoc documentation** with beautiful API documentation

---

## 🧪 Example Usage

### Command Line
```bash
# Full analysis
curl "http://localhost:8000/analyze?path=/home/user/documents"

# Paginated results (5 files, skip first 10)
curl "http://localhost:8000/analyze/files?path=/home/user/documents&limit=5&offset=10"
```

### Interactive Documentation
```bash
# Start the server
uvicorn main:app --reload

# Then visit:
# http://127.0.0.1:8000/docs      - Swagger UI
# http://127.0.0.1:8000/redoc     - ReDoc UI
```

---

## 📂 Output Example

```json
{
  "file_count": 1234,
  "total_size": 56789012,
  "extensions": {
    ".txt": {"count": 320, "size": 1234567},
    ".jpg": {"count": 200, "size": 4567890}
  },
  "largest_files": [
    {"name": "video.mp4", "size": 10240000, "path": "...", "extension": ".mp4", ...}
  ],
  "all_files": [...]
}
```

---

## ⚠️ Notes

* Symlinks are detected but not followed.
* Files with permission issues are skipped with a warning in logs.
* Use valid absolute paths accessible to the service's runtime user.

---

## 🧑‍💻 Author

Pedro Anisio
[Email](mailto:pedroanisio@arc4d3.com) | [ARC4D3](https://arc4d3.com)

---

## 📜 License

MIT License

