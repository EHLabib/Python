#!/usr/bin/env python3

import requests
import re
import os
import csv
import math
import time
import hashlib
import random
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import OrderedDict, Counter
import logging

# ================= CONFIG =================
INPUT_FILE = "domains.txt"
OUTPUT_DIR = "ultra_output"

DEPTH = 2
MAX_PAGES = 500

DOMAIN_THREADS = 3
JS_THREADS = 5
MAX_HTTP_CONCURRENCY = DOMAIN_THREADS * JS_THREADS

MAX_JS_SIZE = 2_000_000
ENTROPY_THRESHOLD = 4.2
RATE_LIMIT_DELAY = 0.3
MAX_CACHE_SIZE = 1000

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, 'scanner.log')),
        logging.StreamHandler()
    ]
)

# ================= RATE LIMITER =================
class RateLimiter:
    def __init__(self, delay, max_concurrency):
        self.delay = delay
        self.last_request = {}
        self.lock = Lock()
        self.semaphore = Semaphore(max_concurrency)

    def wait(self, key):
        with self.lock:
            now = time.time()
            last = self.last_request.get(key, 0)
            sleep_time = self.delay - (now - last)
            
            should_sleep = sleep_time > 0
        
        # Sleep outside the lock to allow other threads to run
        if should_sleep:
            time.sleep(sleep_time + random.uniform(0, 0.1))
            with self.lock:
                self.last_request[key] = time.time()
        else:
            with self.lock:
                # Update timestamp to 'now' so next request waits if needed
                self.last_request[key] = time.time()

    def acquire(self):
        self.semaphore.acquire()

    def release(self):
        self.semaphore.release()

rate_limiter = RateLimiter(RATE_LIMIT_DELAY, MAX_HTTP_CONCURRENCY)

# ================= HASH CACHE =================
class ThreadSafeHashCache:
    def __init__(self, max_size=1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = Lock()

    def seen(self, key):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return True
            return False

    def add(self, key):
        with self.lock:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            self.cache[key] = True

hash_cache = ThreadSafeHashCache(MAX_CACHE_SIZE)

# ================= SESSION =================
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.5,
              status_forcelist=[429,500,502,503,504],
              allowed_methods=["GET","HEAD"])
adapter = HTTPAdapter(max_retries=retry, pool_connections=30, pool_maxsize=30)
session.mount("http://", adapter)
session.mount("https://", adapter)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

# ================= REGEX =================
KEYWORDS = re.compile(r"(api[_-]?key|secret|token|password|bearer|jwt|auth)", re.I)
VALUE = re.compile(r"(?:['\"`])([A-Za-z0-9_\-\.\/=]{24,})(?:['\"`])")
ENDPOINT = re.compile(
    r"(?:['\"`])("
    r"https?://[^'\"`\s]{5,}|"
    r"/(?:api|v1|v2|v3|graphql|auth|admin|internal|rest)[^'\"`\s]{2,}"
    r")(?:['\"`])",
    re.I
)

# ================= ENTROPY =================
def entropy(s):
    if len(s) < 8:
        return 0
    counts = Counter(s)
    length = len(s)
    return -sum((c/length) * math.log2(c/length) for c in counts.values())

def looks_secret(s):
    # Ignore JWTs (usually start with eyJ) to reduce false positives
    if s.startswith("eyJ"):
        return False
    return len(s) >= 24 and entropy(s) > ENTROPY_THRESHOLD

# ================= HELPERS =================
def normalize(url):
    if not url:
        return None
    if not url.startswith("http"):
        url = "https://" + url
    url, _ = urldefrag(url)
    return url.rstrip("/")

def is_subdomain(child, parent):
    try:
        return urlparse(child).netloc.endswith(urlparse(parent).netloc)
    except:
        return False

# ================= FETCH =================
def fetch(url, key):
    rate_limiter.acquire()
    try:
        rate_limiter.wait(key)
        
        # Thread-safe: Generate headers locally
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        r = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        r.raise_for_status()

        content = r.content
        if len(content) > MAX_JS_SIZE:
            logging.debug(f"Skipping {url}: File too large ({len(content)} bytes)")
            return None

        content_type = r.headers.get("Content-Type","").lower()
        if not any(x in content_type for x in ["html","javascript","json","text","xml"]):
            logging.debug(f"Skipping {url}: Unsupported content type {content_type}")
            return None

        return content.decode(errors="ignore")

    except Exception as e:
        logging.debug(f"Error fetching {url}: {e}")
        return None
    finally:
        rate_limiter.release()

# ================= CRAWL =================
def crawl(domain):
    visited = set()
    stack = [(domain, 0)]
    pages = set()
    host = urlparse(domain).netloc

    logging.info(f"Starting crawl for {host}")

    while stack:
        if len(pages) >= MAX_PAGES:
            logging.info(f"Reached max pages limit ({MAX_PAGES}) for {host}")
            break

        url, depth = stack.pop()
        
        # Normalize and validate
        url = normalize(url)
        if not url or url in visited:
            continue

        if depth > DEPTH:
            continue

        visited.add(url)
        html = fetch(url, host)
        
        if not html:
            continue

        pages.add(url)
        logging.debug(f"Crawled ({depth}): {url}")

        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                full = normalize(urljoin(url, a["href"]))
                if full and is_subdomain(full, domain):
                    stack.append((full, depth + 1))
        except Exception as e:
            logging.error(f"Error parsing HTML for {url}: {e}")
            continue

    logging.info(f"Crawl complete. Found {len(pages)} pages.")
    return pages

# ================= JS DISCOVERY =================
def discover_js(page, host):
    js = set()
    html = fetch(page, host)
    if not html:
        return js

    try:
        soup = BeautifulSoup(html, "html.parser")
        for s in soup.find_all("script", src=True):
            src = normalize(urljoin(page, s["src"]))
            if src and (src.endswith(".js") or ".js?" in src):
                js.add(src)
    except Exception as e:
        logging.error(f"Error discovering JS on {page}: {e}")
    
    return js

# ================= ANALYZE =================
def analyze_js(js_url, domain):
    content = fetch(js_url, domain)
    if not content:
        return set(), set()

    # Check Hash Cache
    h = hashlib.md5(content.encode()).hexdigest()
    if hash_cache.seen(h):
        return set(), set()
    hash_cache.add(h)

    secrets = set()
    endpoints = set()

    # Analyze line by line
    for i, line in enumerate(content.splitlines(), 1):
        # Find Endpoints
        for ep in ENDPOINT.findall(line):
            endpoints.add(ep.strip())

        # Find Secrets
        if KEYWORDS.search(line):
            for v in VALUE.findall(line):
                if looks_secret(v):
                    secrets.add((domain, js_url, i, v))

    return secrets, endpoints

# ================= DOMAIN SCAN =================
def scan_domain(domain):
    domain = normalize(domain)
    if not domain:
        return

    host = urlparse(domain).netloc
    logging.info(f"[*] Scanning domain: {host}")

    domain_dir = os.path.join(OUTPUT_DIR, host)
    try:
        os.makedirs(domain_dir, exist_ok=True)
    except OSError as e:
        logging.error(f"Cannot create directory for {host}: {e}")
        return

    secrets_file = os.path.join(domain_dir, "secrets.csv")
    endpoints_file = os.path.join(domain_dir, "endpoints.csv")

    # Crawl to find pages
    pages = crawl(domain)
    
    # Discover JS files
    js = set()
    for p in pages:
        js.update(discover_js(p, host))
    
    logging.info(f"Found {len(js)} JavaScript files. Analyzing...")

    # Analyze JS files
    with ThreadPoolExecutor(max_workers=JS_THREADS) as ex:
        futures = {ex.submit(analyze_js, j, host): j for j in js}

        for f in as_completed(futures):
            js_url = futures[f]
            try:
                secrets, endpoints = f.result()
                
                # Write Secrets (Open/Close once per batch to be efficient but safe)
                if secrets:
                    with open(secrets_file, "a", newline="", encoding="utf-8") as sf:
                        writer = csv.writer(sf)
                        # Write header if empty
                        if sf.tell() == 0:
                            writer.writerow(["domain", "js_file", "line", "value"])
                        
                        for secret in secrets:
                            logging.warning(f"[SECRET FOUND] {secret[3][:20]}... in {secret[1]}")
                            writer.writerow(secret)

                # Write Endpoints
                if endpoints:
                    with open(endpoints_file, "a", newline="", encoding="utf-8") as ef:
                        writer = csv.writer(ef)
                        if ef.tell() == 0:
                            writer.writerow(["domain", "endpoint"])
                        
                        for ep in endpoints:
                            logging.info(f"[ENDPOINT] {ep}")
                            writer.writerow([host, ep])

            except Exception as e:
                logging.error(f"Error analyzing {js_url}: {e}")

    logging.info(f"[+] Finished {host}")

# ================= MAIN =================
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} missing")
        logging.error(f"Input file {INPUT_FILE} not found")
        return

    with open(INPUT_FILE) as f:
        domains = [d.strip() for d in f if d.strip()]

    if not domains:
        print("No domains found in input file.")
        return

    logging.info(f"Loaded {len(domains)} domains. Starting scan...")
    
    with ThreadPoolExecutor(max_workers=DOMAIN_THREADS) as ex:
        futures = [ex.submit(scan_domain, d) for d in domains]
        
        # Wait for all to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Critical error in domain scan: {e}")

    logging.info("All scans complete.")

if __name__ == "__main__":
    main()