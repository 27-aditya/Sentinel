import os
import datetime
from io import BytesIO
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Configuration
PORT = 8001
LOCATION = os.getenv("LOCATION", "DEFAULT_LOCATION")

# Paths
WEB_ROOT = Path("web")
STATIC_PATH = WEB_ROOT / "static"
LOCATION_PATH = STATIC_PATH / LOCATION


# Directory Handler
class DirectoryHandler(SimpleHTTPRequestHandler):
    """Custom handler that displays directory listings with breadcrumb navigation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def list_directory(self, path):
        """Custom HTML directory listing."""
        try:
            list_dir = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        list_dir.sort(key=lambda a: a.lower())
        relative_path = os.path.relpath(path, str(WEB_ROOT))
        if relative_path == ".":
            relative_path = "/"
        else:
            relative_path = "/" + relative_path.replace("\\", "/")

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Sentinel File Server - {relative_path}</title>
<style>
    body {{ font-family: system-ui, sans-serif; margin: 40px; background-color: #f7f7f7; }}
    h1 {{ color: #333; border-bottom: 2px solid #001F3F; padding-bottom: 5px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    th, td {{ padding: 10px 15px; border-bottom: 1px solid #eee; }}
    th {{ background: #001F3F; color: white; text-align: left; }}
    a {{ color: #1565C0; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .folder {{ color: #1E88E5; font-weight: 600; }}
    .image {{ color: #2E7D32; }}
    .size {{ text-align: right; color: #777; }}
    .date {{ color: #777; }}
    .breadcrumb {{ background: white; padding: 8px 10px; border-radius: 5px;
                  margin-bottom: 15px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }}
    .footer {{ text-align: center; color: #999; margin-top: 40px; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>Sentinel File Server</h1>
<div class="breadcrumb">
"""

        # Breadcrumbs
        if relative_path == "/":
            html += '<a href="/">Root</a>'
        else:
            parts = relative_path.strip("/").split("/")
            crumbs = ['<a href="/">Root</a>']
            current = ""
            for part in parts:
                current += "/" + part
                crumbs.append(f'<a href="{current}/">{part}</a>')
            html += " / ".join(crumbs)
        html += "</div>"

        # Table header 
        html += """
        <table>
            <tr><th>Name</th><th>Size</th><th>Modified</th></tr>
        """

        # Parent directory
        if relative_path != "/":
            html += """
            <tr>
                <td><a href="../" class="folder">.. (Parent Directory)</a></td>
                <td class="size">-</td>
                <td class="date">-</td>
            </tr>
            """

        # Folders 
        for name in list_dir:
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                mtime = datetime.datetime.fromtimestamp(os.stat(full_path).st_mtime).strftime("%Y-%m-%d %H:%M")
                html += f"""
                <tr>
                    <td><a href="{name}/" class="folder">{name}/</a></td>
                    <td class="size">-</td>
                    <td class="date">{mtime}</td>
                </tr>
                """

        # Files
        for name in list_dir:
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path):
                stat = os.stat(full_path)
                size = stat.st_size
                size_str = (
                    f"{size} B" if size < 1024
                    else f"{size/1024:.1f} KB" if size < 1024 * 1024
                    else f"{size/(1024*1024):.1f} MB"
                )
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                is_image = name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
                css_class = "image" if is_image else ""
                target = "_blank" if is_image else "_self"
                html += f"""
                <tr>
                    <td><a href="{name}" class="{css_class}" target="{target}">{name}</a></td>
                    <td class="size">{size_str}</td>
                    <td class="date">{mtime}</td>
                </tr>
                """

        # Footer 
        html += f"""
        </table>
        <div class="footer">
            Sentinel File Server | Location: <b>{LOCATION}</b><br>
            Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
</body>
</html>
"""

        encoded = html.encode("utf-8")

        # Wrap in BytesIO so SimpleHTTPRequestHandler can read it
        f = BytesIO(encoded)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f


# Directory Setup
def ensure_directory_structure():
    """Ensure /web/, /web/static/, and /web/static/LOCATION exist."""
    WEB_ROOT.mkdir(exist_ok=True)
    STATIC_PATH.mkdir(exist_ok=True)
    LOCATION_PATH.mkdir(exist_ok=True)
    print("Directory structure ensured:")
    print(f"  - Web root:       {WEB_ROOT.resolve()}")
    print(f"  - Static path:    {STATIC_PATH.resolve()}")
    print(f"  - Location path:  {LOCATION_PATH.resolve()}")
    print("=" * 60)


# Main entrypoint
def main():
    ensure_directory_structure()
    print(f"Starting Sentinel File Server on http://localhost:{PORT}")
    print(f"Serving root: {WEB_ROOT.resolve()}")
    print("Browse files at: http://localhost:8001/")
    print(f"Location files: http://localhost:8001/static/{LOCATION}")
    print("=" * 60)
    try:
        with HTTPServer(("", PORT), DirectoryHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == "__main__":
    main()
