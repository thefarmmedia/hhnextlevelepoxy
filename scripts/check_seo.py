#!/usr/bin/env python3
"""Validate the static site's crawl paths, metadata, schema and legacy URLs.

Run from any directory with Python 3.11+: python3 scripts/check_seo.py
No third-party dependencies or network access are required.
"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import json
import sys
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://hhnextlevelepoxy.com"
ERRORS = []


def require(condition, message):
    if not condition:
        ERRORS.append(message)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.canonicals = []
        self.references = []
        self.h1 = 0
        self.title = ""
        self.in_title = False
        self.in_json = False
        self.json_text = ""
        self.schema = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            self.meta[a.get("name", a.get("property"))] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href"))
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.in_title = True
        if tag == "script" and a.get("type") == "application/ld+json":
            self.in_json = True
            self.json_text = ""
        for attr in ("href", "src", "poster"):
            if a.get(attr):
                self.references.append(a[attr])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_json:
            self.json_text += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_json:
            self.in_json = False
            self.schema.append(json.loads(self.json_text))


urls = [e.text for e in ET.parse(ROOT / "sitemap.xml").iter()
        if e.tag.endswith("}loc")]
require(len(urls) == len(set(urls)), "Sitemap contains duplicate URLs")
pages = {}
titles = Counter()
descriptions = Counter()
for path in sorted(ROOT.glob("*.html")):
    try:
        page = Page(path.read_text())
    except (ValueError, TypeError) as exc:
        ERRORS.append(f"{path.name}: invalid HTML metadata or JSON-LD: {exc}")
        continue
    require(page.h1 == 1, f"{path.name}: expected one main heading")
    require(bool(page.title.strip()), f"{path.name}: missing title")
    require(bool(page.meta.get("description")), f"{path.name}: missing description")
    canonical = BASE + ("/" if path.name == "index.html" else "/" + path.name)
    if path.name == "404.html":
        require("noindex" in page.meta.get("robots", ""), "404 must be noindex")
        require(canonical not in urls, "404 must not be in sitemap")
    else:
        pages[canonical] = page
        require(page.canonicals == [canonical], f"{path.name}: incorrect canonical")
        require("noindex" not in page.meta.get("robots", ""), f"{path.name}: noindex")
        titles[page.title] += 1
        descriptions[page.meta.get("description")] += 1
    for ref in page.references:
        u = urlsplit(urljoin(canonical, ref))
        if u.scheme not in ("http", "https") or u.netloc != urlsplit(BASE).netloc:
            continue
        local = ROOT / unquote(u.path).lstrip("/") if u.path != "/" else ROOT / "index.html"
        require(local.is_file(), f"{path.name}: missing local reference {ref}")
        require(u.path != "/index.html", f"{path.name}: link to redirecting homepage")
    for data in page.schema:
        types = data.get("@type", [])
        types = [types] if isinstance(types, str) else types
        if "BreadcrumbList" in types:
            require(data["itemListElement"][-1].get("item") == canonical,
                    f"{path.name}: final breadcrumb points at a different page")
        if "LocalBusiness" in types:
            require(data.get("address", {}).get("addressLocality") == "Richmond",
                    f"{path.name}: inconsistent business locality")
            require("geo" not in data, f"{path.name}: unverified business coordinates")
            require("aggregateRating" not in data and "review" not in data,
                    f"{path.name}: self-serving review markup")
    require("no contact info" not in path.read_text().lower(),
            f"{path.name}: calculator promise contradicts contact gate")

require(set(urls) == set(pages), "Sitemap does not match the indexable HTML pages")
require(all(v == 1 for v in titles.values()), "Duplicate page titles")
require(all(v == 1 for v in descriptions.values()), "Duplicate page descriptions")

redirects = {}
for line in (ROOT / "_redirects").read_text().splitlines():
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    source, target, status, *_ = line.split()
    require(source not in redirects, f"Duplicate redirect source: {source}")
    redirects[source] = (target, status)
    if source.startswith("/") and "*" not in source and target.startswith("/"):
        require(source != target, f"Redirect loop: {source}")
        dest = ROOT / target.lstrip("/") if target != "/" else ROOT / "index.html"
        require(dest.is_file(), f"Redirect destination is missing: {source} -> {target}")

# These eight URLs were confirmed as live 404s in Search Console on 2026-10-21.
legacy = {
    "/areas/kearney": "/areas-kearney.html",
    "/areas/richmond": "/areas-richmond.html",
    "/services/residential/garage-floor-coatings": "/services-residential-garage-floor-coatings.html",
    "/about-us": "/about.html",
    "/blog/how-to-clean-epoxy-floor": "/blog-how-to-clean-epoxy-floor.html",
    "/chillicothe-mo-epoxy-flooring-419759": "/areas-chillicothe.html",
    "/richmond.html": "/areas-richmond.html",
    "/contact-us-4101": "/contact.html",
}
for source, target in legacy.items():
    require(redirects.get(source) == (target, "301!"), f"Missing legacy recovery: {source}")
require(redirects.get("/*") == ("/404.html", "404"), "Unknown URLs must retain real 404s")
config = tomllib.loads((ROOT / "netlify.toml").read_text())
require(config["build"]["processing"]["html"]["pretty_urls"] is False,
        "Pretty URLs conflict with the site's .html canonicals")
require("Sitemap: " + BASE + "/sitemap.xml" in (ROOT / "robots.txt").read_text(),
        "robots.txt is missing the canonical sitemap")

if ERRORS:
    print("SEO checks failed:\n" + "\n".join("- " + e for e in ERRORS))
    sys.exit(1)
print(f"SEO checks passed: {len(pages)} indexable pages, {len(urls)} sitemap URLs, "
      f"{len(redirects)} routing rules, all 8 Search Console 404 recoveries.")
