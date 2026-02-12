"""Simple HTTP server that serves site/ as root with data/ mounted at /data/."""

import os
import http.server
import shutil
import sys
import tempfile

def main():
    # Create a temporary directory with the right structure
    tmpdir = tempfile.mkdtemp()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Copy site/ contents to tmpdir
    site_dir = os.path.join(project_root, "site")
    for item in os.listdir(site_dir):
        src = os.path.join(site_dir, item)
        dst = os.path.join(tmpdir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Copy data/ to tmpdir/data/
    data_src = os.path.join(project_root, "data")
    data_dst = os.path.join(tmpdir, "data")
    if os.path.exists(data_src):
        shutil.copytree(data_src, data_dst)

    os.chdir(tmpdir)
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("", 8080), handler)
    print(f"Serving at http://localhost:8080 from {tmpdir}")
    server.serve_forever()

if __name__ == "__main__":
    main()
