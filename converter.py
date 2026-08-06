#!/usr/bin/env python3
"""
Convert Stuffed18's IPA Archive database into an AltStore-compatible source.

Source database:
https://github.com/stuffed18/ipa-archive-updated

Output:
apps.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

IPA_DB_URL = "https://raw.githubusercontent.com/stuffed18/ipa-archive-updated/main/data/ipa.json"
BASE_URLS_URL = "https://raw.githubusercontent.com/stuffed18/ipa-archive-updated/main/data/urls.json"
ICON_ROOT = "https://stuffed18.github.io/ipa-archive-updated/data"
FALLBACK_ICON = "https://stuffed18.github.io/ipa-archive-updated/apple-touch-icon.png"

SOURCE_NAME = "FastHoppers IPA Archive"
SOURCE_IDENTIFIER = "com.fasthoppers.ipaarchive"
SOURCE_SUBTITLE = "AltStore-compatible index generated from Stuffed18's IPA Archive"
SOURCE_DESCRIPTION = (
    "An automatically generated source containing apps indexed by Stuffed18's "
    "IPA Archive. Files are hosted by their original third-party archives."
)


def download_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FastHoppers-IPA-Archive-Converter/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def minimum_os(number: Any) -> str:
    try:
        value = int(number)
    except (TypeError, ValueError):
        return "1.0"

    major = value // 10000
    minor = (value // 100) % 100
    patch = value % 100

    if patch:
        return f"{major}.{minor}.{patch}"
    return f"{major}.{minor}"


def version_sort_key(version: str) -> tuple:
    parts = []
    for part in str(version).split(" ", 1)[0].replace("-", ".").split("."):
        try:
            parts.append((0, int(part)))
        except ValueError:
            parts.append((1, part.lower()))
    return tuple(parts)


def safe_version(version: Any) -> str:
    value = str(version or "1.0").strip()
    return value.split(" ", 1)[0] or "1.0"


def encode_download_url(base: str, path: str) -> str:
    # Preserve slashes but encode spaces, #, ?, Unicode, etc.
    encoded_path = urllib.parse.quote(str(path), safe="/()[]-_.~")
    return base.rstrip("/") + "/" + encoded_path.lstrip("/")


def icon_url(entry: list[Any]) -> str:
    pk = int(entry[0])
    image_pk = entry[9] if len(entry) > 9 and entry[9] is not None else pk
    try:
        image_pk = int(image_pk)
    except (TypeError, ValueError):
        return FALLBACK_ICON
    return f"{ICON_ROOT}/{image_pk // 1000}/{image_pk}.jpg?v=2"


def convert_entry(entry: list[Any], base_urls: dict[str, str]) -> dict[str, Any] | None:
    # Schema:
    # [pk, platform, minOS, title, bundleId, version, baseUrl, pathName, size, optionalImagePk]
    if len(entry) < 9:
        return None

    pk, platform, min_os, title, bundle_id, version, base_id, path_name, size = entry[:9]

    bundle_id = str(bundle_id or "").strip()
    title = str(title or "").strip()
    path_name = str(path_name or "").strip()
    base = base_urls.get(str(base_id))

    if not bundle_id or not title or not path_name or not base:
        return None

    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 0

    return {
        "pk": int(pk),
        "name": title,
        "bundleIdentifier": bundle_id,
        "developerName": "Unknown / archived",
        "localizedDescription": (
            f"Archived IPA indexed by Stuffed18. Original filename: "
            f"{path_name.rsplit('/', 1)[-1]}"
        ),
        "iconURL": icon_url(entry),
        "version": {
            "version": safe_version(version),
            "date": "2000-01-01",
            "localizedDescription": "Archived release",
            "downloadURL": encode_download_url(base, path_name),
            "size": max(size, 1),
            "minOSVersion": minimum_os(min_os),
        },
    }


def build_source(
    entries: list[list[Any]],
    base_urls: dict[str, str],
    latest_only: bool,
    max_apps: int | None,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    skipped = 0
    for raw in entries:
        converted = convert_entry(raw, base_urls)
        if converted is None:
            skipped += 1
            continue
        grouped[converted["bundleIdentifier"]].append(converted)

    apps: list[dict[str, Any]] = []
    for bundle_id, releases in grouped.items():
        releases.sort(
            key=lambda item: (
                version_sort_key(item["version"]["version"]),
                item["pk"],
            ),
            reverse=True,
        )

        newest = releases[0]
        versions = [r["version"] for r in releases]
        if latest_only:
            versions = versions[:1]

        app = {
            "name": newest["name"],
            "bundleIdentifier": bundle_id,
            "developerName": newest["developerName"],
            "subtitle": "Archived iOS app",
            "localizedDescription": newest["localizedDescription"],
            "iconURL": newest["iconURL"],
            "tintColor": "D2691E",
            "versions": versions,
            "appPermissions": {
                "entitlements": [],
                "privacy": {}
            },
        }
        apps.append(app)

    apps.sort(key=lambda app: app["name"].casefold())
    if max_apps is not None:
        apps = apps[:max_apps]

    print(
        f"Generated {len(apps)} apps from {len(entries)} records "
        f"({skipped} invalid records skipped).",
        file=sys.stderr,
    )

    return {
        "name": SOURCE_NAME,
        "identifier": SOURCE_IDENTIFIER,
        "subtitle": SOURCE_SUBTITLE,
        "description": SOURCE_DESCRIPTION,
        "website": "https://stuffed18.github.io/ipa-archive-updated/",
        "sourceURL": "https://FastHoppers.github.io/ipa-archive-source/apps.json",
        "iconURL": FALLBACK_ICON,
        "headerURL": FALLBACK_ICON,
        "tintColor": "D2691E",
        "featuredApps": [app["bundleIdentifier"] for app in apps[:8]],
        "apps": apps,
        "news": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", default="apps.json")
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Keep only the newest indexed version of each bundle ID.",
    )
    parser.add_argument(
        "--max-apps",
        type=int,
        default=None,
        help="Limit output for testing, e.g. --max-apps 100.",
    )
    args = parser.parse_args()

    entries = download_json(IPA_DB_URL)
    base_urls = download_json(BASE_URLS_URL)

    source = build_source(
        entries=entries,
        base_urls=base_urls,
        latest_only=args.latest_only,
        max_apps=args.max_apps,
    )

    output = Path(args.output)
    output.write_text(
        json.dumps(source, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {output} ({output.stat().st_size:,} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
