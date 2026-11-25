#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam, Naver) which pages of the guide changed.

Run by the indexnow job of .github/workflows/pages.yml after each deploy.

  indexnow.py changed   pages whose source changed in the deployed commit (default)
  indexnow.py all       every page of the guide

A change to build.py or assets/ counts as a change to every page. The first deploy
that publishes the key file submits every page once. Google does not use IndexNow;
Search Console stays the route for Google. Never fails the workflow: a refusal is
printed as a warning, since the site itself is already deployed.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (same pages, slugs and BASE_URL as the deployed site)

ENDPOINT = "https://api.indexnow.org/indexnow"


def all_urls() -> list[str]:
    return [build.BASE_URL + build.url_of(lang, pid) for lang in build.LANGS for pid in build.SITE[lang]]


def changed_files() -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", "HEAD^1", "HEAD"],
                         capture_output=True, text=True, check=True).stdout
    return out.split()


def key_is_new() -> bool:
    previous = subprocess.run(["git", "show", "HEAD^1:build.py"], capture_output=True, text=True).stdout
    return build.INDEXNOW_KEY not in previous


def changed_urls() -> list[str]:
    if key_is_new():
        print("Key file is new in this deploy: submitting every page once.")
        return all_urls()
    files = changed_files()
    if any(f == "build.py" or f.startswith("assets/") for f in files):
        return all_urls()
    urls = []
    for f in files:
        m = re.match(r"^content/([a-z]{2})/(.+)$", f)
        if not m or m.group(1) not in build.LANGS or not (ROOT / f).exists():
            continue
        lang, name = m.groups()
        if name == "home.yml":
            pid = "home"
        else:
            front = re.match(r"^---\n(.*?)\n---\n", (ROOT / f).read_text(encoding="utf-8"), re.S)
            pid = build.yaml.safe_load(front.group(1))["id"] if front else None
        if pid in build.SITE[lang]:
            urls.append(build.BASE_URL + build.url_of(lang, pid))
    return urls


def main() -> None:
    scope = sys.argv[1] if len(sys.argv) > 1 else "changed"
    base = urlparse(build.BASE_URL)
    if base.path not in ("", "/"):
        print(f"Site is served from {build.BASE_URL}, not from its own domain: IndexNow skipped.")
        return
    urls = sorted(set(all_urls() if scope == "all" else changed_urls()))
    if not urls:
        print("No page changed in this deploy; nothing to submit.")
        return
    payload = {"host": base.netloc, "key": build.INDEXNOW_KEY,
               "keyLocation": f"{build.BASE_URL}/{build.INDEXNOW_KEY}.txt", "urlList": urls}
    time.sleep(30)  # let the new deploy, and the key file, go live first
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json; charset=utf-8"},
                                     method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"IndexNow answered {response.status} for {len(urls)} URL(s):")
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        detail = error.read().decode("utf-8", "replace")[:300] if hasattr(error, "read") else str(error)
        print(f"::warning::IndexNow did not accept the submission: {getattr(error, 'code', '')} {detail}")
        return
    for url in urls:
        print(" ", url)


if __name__ == "__main__":
    main()
