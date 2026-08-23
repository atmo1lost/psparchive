import argparse
import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

SOURCES = {
    "plugins": "https://www.gamebrew.org/wiki/List_of_PSP_plugins",
    "ptf": "https://www.pspunk.com/psp-ptf-themes/",
    "ctf": "https://www.pspunk.com/psp-ctf-themes/",
}

REQUEST_DELAY = 0.5


def slugify(title):
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fetch(url, referer=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    }

    if referer:
        headers["Referer"] = referer

    request = urllib.request.Request(
        url,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()

            charset = response.headers.get_content_charset()

            if charset:
                return raw.decode(charset, errors="replace")

            return raw.decode("utf-8", errors="replace")

    except Exception as e:
        print(f"    [!] Failed to fetch {url}")
        print(f"        {e}")
        return None


def is_downloadable(url):
    """
    Your exact rule:

    - URL must contain a filename with a dot
    - .html and .htm are rejected
    """

    path = urllib.parse.urlparse(url).path.lower()
    filename = Path(path).name

    if "." not in filename:
        return False

    if filename.endswith((".html", ".htm")):
        return False

    return True


def absolute_url(url, base):
    return urllib.parse.urljoin(base, url)


def load_json(kind):
    path = Path(f"{kind}.json")

    if not path.exists():
        print(f"[!] {path} does not exist.")
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[!] Could not read {path}: {e}")
        sys.exit(1)


def existing_info(kind):
    """
    Build duplicate sets from the existing JSON.

    Checks:
      - slug
      - title
      - download URL
      - download filename
    """

    items = load_json(kind)

    slugs = set()
    titles = set()
    urls = set()
    filenames = set()

    for item in items:
        slug = str(item.get("slug", "")).strip().lower()
        title = str(item.get("title", "")).strip().lower()
        download = str(item.get("download", "")).strip()

        if slug:
            slugs.add(slug)

        if title:
            titles.add(title)

        if download:
            urls.add(download.lower())

            filename = Path(
                urllib.parse.urlparse(download).path
            ).name.lower()

            if filename:
                filenames.add(filename)

    return items, slugs, titles, urls, filenames


def local_file_exists(kind, slug):
    """
    Catch files left over from an interrupted import,
    even if they aren't in JSON yet.
    """

    files_dir = Path(kind) / "files"
    thumbs_dir = Path(kind) / "thumbs"

    if files_dir.exists():
        if any(files_dir.glob(f"{slug}.*")):
            return True

    if thumbs_dir.exists():
        if any(thumbs_dir.glob(f"{slug}.*")):
            return True

    return False

def encode_url(url):
    parsed = urllib.parse.urlsplit(url)

    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        urllib.parse.quote(
            parsed.path,
            safe="/",
        ),
        parsed.query,
        parsed.fragment,
    ))

def download(url, destination, referer=None):
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Never overwrite an existing file.
    if destination.exists():
        print(f"    [=] File already exists: {destination}")
        return False

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }

    if referer:
        headers["Referer"] = referer

    request = urllib.request.Request(
        url,
        headers=headers,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".part"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with open(temporary, "wb") as output:
                shutil.copyfileobj(
                    response,
                    output,
                    64 * 1024,
                )

        temporary.replace(destination)

        return True

    except Exception as e:
        print(f"    [!] Download failed: {e}")

        if temporary.exists():
            temporary.unlink()

        return False


# ---------------------------------------------------------
# GAMEBREW
# ---------------------------------------------------------

def parse_gamebrew(url):
    html = fetch(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    entries = []
    seen = set()

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])

            if not cells:
                continue

            link = cells[0].find("a", href=True)

            if not link:
                continue

            title = link.get_text(" ", strip=True)
            page = absolute_url(link["href"], url)

            if not title:
                continue

            if "/wiki/" not in urllib.parse.urlparse(page).path:
                continue

            if page in seen:
                continue

            seen.add(page)

            description = ""

            if len(cells) >= 2:
                description = cells[1].get_text(
                    " ",
                    strip=True,
                )

            entries.append({
                "title": title,
                "page": page,
                "description": description,
            })

    return entries


def parse_gamebrew_page(entry):
    html = fetch(entry["page"])

    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    thumbnail = None

    og = soup.find(
        "meta",
        attrs={"property": "og:image"},
    )

    if og and og.get("content"):
        thumbnail = absolute_url(
            og["content"],
            entry["page"],
        )

    downloads = []

    for link in soup.find_all("a", href=True):
        url = absolute_url(
            link["href"],
            entry["page"],
        )

        if is_downloadable(url):
            downloads.append(url)

    if not downloads:
        return None

    # Prefer obvious archive/plugin files.
    preferred = (
        ".zip",
        ".7z",
        ".rar",
        ".prx",
        ".ptf",
        ".ctf",
    )

    download_url = None

    for url in downloads:
        if urllib.parse.urlparse(
            url
        ).path.lower().endswith(preferred):
            download_url = url
            break

    if not download_url:
        download_url = downloads[0]

    return {
        "title": entry["title"],
        "description": entry["description"],
        "thumbnail": thumbnail,
        "download": download_url,
        "source": entry["page"],
    }


# ---------------------------------------------------------
# PSPUNK
# ---------------------------------------------------------

def parse_pspunk(url):
    html = fetch(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    entries = []
    seen = set()

    # PSPunk's PTF page has theme cards containing:
    # thumbnail + theme title + download link.
    for image in soup.find_all("img"):
        src = (
            image.get("data-src")
            or image.get("data-lazy-src")
            or image.get("src")
        )

        if not src:
            continue

        # Find the nearest useful container.
        container = image.find_parent(
            ["article", "li", "div"]
        )

        if not container:
            continue

        text = container.get_text(
            " ",
            strip=True,
        )

        # Find a .ptf link inside the same card/container.
        download_link = None

        for link in container.find_all(
            "a",
            href=True,
        ):
            href = absolute_url(
                link["href"],
                url,
            )

            href = encode_url(href)

            path = urllib.parse.urlparse(
                href
            ).path.lower()

            if path.endswith(".ptf"):
                download_link = href
                break

        if not download_link:
            continue

        # Use the link/card text as the title.
        title = ""

        for link in container.find_all(
            "a",
            href=True,
        ):
            link_text = link.get_text(
                " ",
                strip=True,
            )

            if (
                link_text
                and not link_text.lower().endswith(".ptf")
            ):
                title = link_text
                break

        if not title:
            filename = Path(
                urllib.parse.urlparse(
                    download_link
                ).path
            ).stem

            title = filename.replace(
                "__",
                " ",
            ).replace(
                "_",
                " ",
            )

        if download_link in seen:
            continue

        seen.add(download_link)

        thumbnail = absolute_url(
            src,
            url,
        )

        entries.append({
            "title": title,
            "page": download_link,
            "thumbnail": thumbnail,
        })

    return entries


def parse_pspunk_page(entry, kind):
    download_url = entry["page"]

    if not is_downloadable(download_url):
        return None

    path = urllib.parse.urlparse(download_url).path.lower()

    if kind == "ptf" and not path.endswith(".ptf"):
        return None

    if kind == "ctf" and not path.endswith(".ctf"):
        return None

    return {
        "title": entry["title"],
        "description": " ",
        "compat": ["ptf"],
        "thumbnail": entry.get("thumbnail"),
        "download": download_url,
        "source": "https://www.pspunk.com/psp-ptf-themes/",
    }


# ---------------------------------------------------------
# IMPORT
# ---------------------------------------------------------

def import_entries(kind, source_type, amount):
    json_kind = "themes" if kind in ("ptf", "ctf") else "plugins"

    items, slugs, titles, urls, filenames = (
        existing_info(json_kind)
    )

    print(
        f"\nExisting {json_kind}: {len(items)}"
    )

    # Get listing.
    if source_type == "gamebrew":
        listing = parse_gamebrew(
            SOURCES["plugins"]
        )
    else:
        listing = parse_pspunk(
            SOURCES[kind]
        )

    print(
        f"Found {len(listing)} entries on source."
    )

    candidates = []

    for entry in listing:
        title = entry["title"]
        slug = slugify(title)

        # JSON duplicate checks BEFORE fetching
        # individual pages.
        if slug in slugs:
            continue

        if title.lower() in titles:
            continue

        candidates.append(entry)

    print(
        f"New candidates: {len(candidates)}"
    )

    if not candidates:
        print("Nothing new to import.")
        return

    # User chooses amount.
    while True:
        answer = input(
            f"\nHow many do you want to import? "
            f"(1-{len(candidates)}, 'all', 0=cancel): "
        ).strip().lower()

        if answer == "0":
            print("Cancelled.")
            return

        if answer == "all":
            amount = len(candidates)
            break

        try:
            amount = int(answer)

            if 1 <= amount <= len(candidates):
                break

        except ValueError:
            pass

        print(
            f"Please enter a number from "
            f"1 to {len(candidates)}, "
            f"'all', or 0."
        )

    candidates = candidates[:amount]

    added = 0
    skipped = 0
    failed = 0

    for number, entry in enumerate(
        candidates,
        start=1,
    ):
        print(
            f"\n[{number}/{amount}] "
            f"{entry['title']}"
        )

        slug = slugify(entry["title"])

        # Check AGAIN immediately before download.
        if slug in slugs:
            print("  [=] Already exists, skipping.")
            skipped += 1
            continue

        if entry["title"].lower() in titles:
            print("  [=] Title already exists, skipping.")
            skipped += 1
            continue

        if local_file_exists(
            json_kind,
            slug,
        ):
            print(
                "  [=] Local file already exists, skipping."
            )
            skipped += 1
            continue

        # Get individual page.
        if source_type == "gamebrew":
            data = parse_gamebrew_page(entry)
        else:
            data = parse_pspunk_page(
                entry,
                kind,
            )

        if not data:
            print(
                "  [!] No valid download found."
            )
            failed += 1
            continue

        download_url = data["download"]

        # URL duplicate.
        if download_url.lower() in urls:
            print(
                "  [=] Same download URL already "
                "exists in JSON, skipping."
            )
            skipped += 1
            continue

        # Filename duplicate.
        filename = Path(
            urllib.parse.urlparse(
                download_url
            ).path
        ).name.lower()

        if filename in filenames:
            print(
                f"  [=] Same filename already exists "
                f"({filename}), skipping."
            )
            skipped += 1
            continue

        print(f"  Download: {download_url}")

        files_dir = (
            Path(json_kind) / "files"
        )

        thumbs_dir = (
            Path(json_kind) / "thumbs"
        )

        files_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        thumbs_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = Path(
            urllib.parse.urlparse(
                download_url
            ).path
        ).suffix

        if not extension:
            extension = ".bin"

        file_destination = (
            files_dir / f"{slug}{extension}"
        )

        # Final filesystem safety check.
        if file_destination.exists():
            print(
                "  [=] Destination already exists."
            )
            skipped += 1
            continue

        if not download(
            download_url,
            file_destination,
            data["source"],
        ):
            failed += 1
            continue

        thumb_path = ""

        if data.get("thumbnail"):
            thumb_url = data["thumbnail"]

            thumb_ext = Path(
                urllib.parse.urlparse(
                    thumb_url
                ).path
            ).suffix.lower()

            if thumb_ext not in (
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".gif",
            ):
                thumb_ext = ".jpg"

            thumb_destination = (
                thumbs_dir /
                f"{slug}{thumb_ext}"
            )

            if download(
                thumb_url,
                thumb_destination,
                data["source"],
            ):
                thumb_path = str(
                    thumb_destination
                )

        item = {
            "slug": slug,
            "title": data["title"],
            "description": data["description"],
            "compat": ["1000", "2000", "3000", "Go"],
            "thumb": thumb_path,
            "download": str(file_destination),
        }

        items.append(item)

        # Update duplicate indexes immediately.
        slugs.add(slug)
        titles.add(data["title"].lower())
        urls.add(download_url.lower())
        filenames.add(filename)

        Path(
            f"{json_kind}.json"
        ).write_text(
            json.dumps(
                items,
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        added += 1

        print("  [+] Added!")

        time.sleep(REQUEST_DELAY)

    print("\n==============================")
    print("Import finished")
    print("==============================")
    print(f"Added:   {added}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")


def main():
    parser = argparse.ArgumentParser(
        description="PSP Archive bulk importer"
    )

    parser.add_argument(
        "--source",
        choices=("plugins", "ptf", "ctf"),
        required=True,
        help="What to import",
    )

    args = parser.parse_args()

    if args.source == "plugins":
        import_entries(
            "plugins",
            "gamebrew",
            0,
        )

    elif args.source == "ptf":
        import_entries(
            "ptf",
            "pspunk",
            0,
        )

    elif args.source == "ctf":
        import_entries(
            "ctf",
            "pspunk",
            0,
        )


if __name__ == "__main__":
    main()