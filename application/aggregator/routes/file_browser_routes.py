import os
import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter()

# These will be injected from main
STATIC_PATH = None
templates = None
LOCATION = None

def init_file_browser(static_path, templates_ref, location):
    global STATIC_PATH, templates, LOCATION
    STATIC_PATH = static_path
    templates = templates_ref
    LOCATION = location

@router.get("/", response_class=HTMLResponse)
async def file_browser(request: Request, subpath: str = ""):
    """Browse local static files with breadcrumbs."""
    full_path = STATIC_PATH / subpath
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    # Serve file directly
    if full_path.is_file():
        return FileResponse(full_path)

    # Build folder + file listings
    items = os.listdir(full_path)
    folders, files = [], []

    for name in sorted(items, key=lambda a: a.lower()):
        p = full_path / name
        mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        if p.is_dir():
            folders.append({
                "name": name,
                "href": f"/?subpath={subpath + '/' + name if subpath else name}",
                "mtime": mtime
            })
        else:
            size = p.stat().st_size
            size_str = (
                f"{size} B" if size < 1024
                else f"{size/1024:.1f} KB" if size < 1024 * 1024
                else f"{size/(1024*1024):.1f} MB"
            )
            files.append({
                "name": name,
                "href": f"/static/{subpath + '/' + name if subpath else name}",
                "size_str": size_str,
                "mtime": mtime,
                "is_image": name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
            })

    # Breadcrumbs
    parts = subpath.strip("/").split("/") if subpath else []
    breadcrumbs = [{"name": "Root", "href": "/"}]
    current = ""
    for part in parts:
        current += "/" + part
        breadcrumbs.append({"name": part, "href": f"/?subpath={current.strip('/')}"})

    parent_dir = None
    if subpath:
        parent_dir = f"/?subpath={'/'.join(parts[:-1])}" if len(parts) > 1 else "/"

    return templates.TemplateResponse("file_browser.html", {
        "request": request,
        "relative_path": subpath or "/",
        "folders": folders,
        "files": files,
        "breadcrumbs": breadcrumbs,
        "parent_dir": parent_dir,
        "location": LOCATION,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
