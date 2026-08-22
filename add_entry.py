import json
import re
import sys
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
 
def slugify(title):
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
 
def fetch_to_path(url, dest_path, chunk_size=1024 * 64):
    parsed = urllib.parse.urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": referer,
        "Accept": "*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out:
        shutil.copyfileobj(resp, out, chunk_size)
 
def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default
 
def save_from_source(source, kind, slug, subfolder):
    """download a url or copy a local file into kind/subfolder/slug.ext, return the repo path or None"""
    if not source:
        return None
 
    out_dir = Path(kind) / subfolder
    out_dir.mkdir(parents=True, exist_ok=True)
 
    if source.startswith("http://") or source.startswith("https://"):
        ext = Path(source.split("?")[0]).suffix or ".bin"
        dest = out_dir / f"{slug}{ext}"
        print(f"downloading {source} -> {dest} ...")
        try:
            fetch_to_path(source, dest)
        except urllib.error.HTTPError as e:
            print(f"error: server refused the download (HTTP {e.code}). "
                  f"the host may be blocking scripted downloads. "
                  f"download it manually in a browser and re-run pointing at the local file instead.")
            sys.exit(1)
        size = dest.stat().st_size
        print(f"saved {dest} ({size} bytes)")
        if size < 5000:
            head = dest.read_bytes()[:200].lower()
            if b"<html" in head or b"<!doctype" in head:
                print("warning: this looks like an html page, not the real file. "
                      "the site likely blocked the download with a bot check. "
                      "download it manually in a browser and re-run pointing at the local file instead.")
        return str(dest)
 
    src = Path(source).expanduser()
    if not src.exists():
        print(f"error: {src} not found")
        sys.exit(1)
    ext = src.suffix or ".bin"
    dest = out_dir / f"{slug}{ext}"
    shutil.copy(src, dest)
    print(f"copied {src} -> {dest}")
    return str(dest)
 
def main():
    print("add a theme or plugin entry\n")
 
    kind = ask("themes or plugins", "themes").lower()
    while kind not in ("themes", "plugins"):
        kind = ask("please type 'themes' or 'plugins'").lower()
 
    json_path = Path(f"{kind}.json")
    if not json_path.exists():
        print(f"error: {json_path} not found, run this from the site root")
        sys.exit(1)
 
    items = json.loads(json_path.read_text())
 
    title = ask("title")
    while not title:
        title = ask("title can't be blank, title")
 
    slug = slugify(title)
    if any(i["slug"] == slug for i in items):
        print(f"error: an entry with slug '{slug}' already exists")
        sys.exit(1)
 
    desc = ask("short description")
    compat_raw = ask("compatible models, comma separated (e.g. 1000,2000,3000,go)")
 
    thumb_source = ask("screenshot, paste a url to download, a local file path, or leave blank for placeholder")
    thumb = save_from_source(thumb_source, kind, slug, "thumbs") or ""
 
    file_source = ask("file source, paste a url to download, a local file path, or leave blank to skip")
    download = save_from_source(file_source, kind, slug, "files") or "#"
 
    entry = {
        "slug": slug,
        "title": title,
        "description": desc,
        "compat": [c.strip() for c in compat_raw.split(",") if c.strip()],
        "thumb": thumb,
        "download": download,
    }
 
    items.append(entry)
    json_path.write_text(json.dumps(items, indent=2) + "\n")
    print(f"\nadded '{title}' to {json_path} (slug: {slug})")
 
if __name__ == "__main__":
    main()