#!/usr/bin/env python3
"""
Fast Multi-Layer Encoding Generator
Recursively applies encodings to generate variations
"""

import base64
import urllib.parse
import html
import sys
import threading
import time
import signal
import codecs
from concurrent.futures import ThreadPoolExecutor

# ----------------------
# CLI Arguments
# ----------------------

if len(sys.argv) < 2:
    print("Usage: python3 fast_encode.py \"payload\" [max_results] [max_layers]")
    print("Example: python3 fast_encode.py \"<script>alert(1)</script>\" 5000 8")
    sys.exit(1)

payload = sys.argv[1]
MAX_RESULTS = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
MAX_LAYERS = int(sys.argv[3]) if len(sys.argv) > 3 else 10
THREADS = 8
MAX_QUEUE_SIZE = 2000
MAX_PAYLOAD_LENGTH = 10000

# ----------------------
# Encoding functions
# ----------------------

def b64(x): return base64.b64encode(x.encode()).decode()
def b32(x): 
    try: return base64.b32encode(x.encode()).decode()
    except: return x
def b16(x): return base64.b16encode(x.encode()).decode()
def url(x): return urllib.parse.quote(x)
def url_plus(x): return urllib.parse.quote_plus(x)
def url_double(x): return urllib.parse.quote(urllib.parse.quote(x))
def hexenc(x): return x.encode().hex()
def hex_upper(x): return x.encode().hex().upper()
def htmlenc(x): return html.escape(x)
def xml_escape(x): return x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
def reverse(x): return x[::-1]
def binary(x): return ''.join(format(ord(c), '08b') for c in x)
def octal(x): return ''.join(format(ord(c), '03o') for c in x)
def unicode_escape(x): return x.encode('unicode_escape').decode()
def rot13(x): return codecs.encode(x, 'rot_13')
def ascii85(x): return base64.a85encode(x.encode()).decode()
def js_escape(x): return x.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
def url_encode_all(x): return ''.join(f'%{ord(c):02X}' for c in x)
def decimal(x): return ''.join(str(ord(c)) for c in x)

encoders = [
    b64, b32, b16, url, url_plus, url_double,
    hexenc, hex_upper, htmlenc, xml_escape,
    reverse, binary, octal, unicode_escape,
    rot13, ascii85, js_escape, url_encode_all, decimal
]

# ----------------------
# Global State
# ----------------------

results = set([payload])
queue = [(payload, 0)]
lock = threading.Lock()
stop_flag = threading.Event()

# ----------------------
# Safe filename generator
# ----------------------

def safe_filename(text):
    return "".join(c for c in text if c.isalnum() or c in '_-')[:20]

# ----------------------
# Signal handler
# ----------------------

def signal_handler(sig, frame):
    print("\n\n[!] Interrupted by user. Saving results...")
    stop_flag.set()
    save_results()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ----------------------
# Progress bar
# ----------------------

def progress_updater():
    while not stop_flag.is_set():
        with lock:
            current = len(results)
            percent = min(1.0, current / MAX_RESULTS)
            bar_len = 30
            filled = int(bar_len * percent)
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"\r[{bar}] {int(percent*100)}% | {current}/{MAX_RESULTS} | Queue: {len(queue)}", end="", flush=True)
            if current >= MAX_RESULTS:
                break
        time.sleep(0.3)

# ----------------------
# Worker
# ----------------------

def process(item):
    current, depth = item

    if depth >= MAX_LAYERS or stop_flag.is_set():
        return []

    new_items = []

    for enc in encoders:
        try:
            new = enc(current)
            if new == current or not new:
                continue
            if len(new) > MAX_PAYLOAD_LENGTH:
                continue

            with lock:
                if new not in results and len(results) < MAX_RESULTS:
                    results.add(new)
                    if depth + 1 < MAX_LAYERS:
                        new_items.append((new, depth + 1))
                    if len(results) >= MAX_RESULTS:
                        stop_flag.set()
                        break
        except Exception:
            continue

    return new_items

# ----------------------
# Save function
# ----------------------

def save_results():
    name = safe_filename(payload)
    output_file = f"encoded_{name}_{len(results)}.txt"

    try:
        with open(output_file, "w", encoding="utf-8", errors='ignore') as f:
            for r in sorted(results):
                try:
                    clean_r = ''.join(char for char in r if ord(char) >= 32 or char in '\n\r\t')
                    f.write(clean_r + "\n")
                except:
                    f.write("[ENCODING ERROR]\n")
    except Exception as e:
        print(f"\n[!] Error saving file: {e}")
        print("\nResults (first 100):")
        for i, r in enumerate(sorted(results)[:100]):
            print(f"{i+1}: {r[:100]}")

    print(f"\n\n[+] Saved {len(results)} encodings to {output_file}")

# ----------------------
# Main execution
# ----------------------

def main():
    global queue
    print(f"[*] Generating encodings for: {payload[:50]}{'...' if len(payload)>50 else ''}")
    print(f"[*] Max results: {MAX_RESULTS}, Max layers: {MAX_LAYERS}, Threads: {THREADS}")
    print(f"[*] Max queue size: {MAX_QUEUE_SIZE}, Max payload length: {MAX_PAYLOAD_LENGTH}")
    print("[*] Press Ctrl+C to stop and save\n")

    progress_thread = threading.Thread(target=progress_updater, daemon=True)
    progress_thread.start()

    iteration = 0
    last_result_count = 0

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        while queue and not stop_flag.is_set() and len(results) < MAX_RESULTS:
            iteration += 1
            if len(results) == last_result_count and iteration > 3:
                print("\n[!] No new unique encodings generated. Stopping...")
                break
            last_result_count = len(results)

            current_batch = queue[:MAX_QUEUE_SIZE]
            queue = queue[MAX_QUEUE_SIZE:]

            if not current_batch:
                break

            futures = list(executor.map(process, current_batch))

            for items in futures:
                if len(queue) < MAX_QUEUE_SIZE:
                    queue.extend(items)
                else:
                    break
                if stop_flag.is_set():
                    break

    stop_flag.set()
    time.sleep(0.2)
    save_results()

    if results:
        avg_len = sum(len(r) for r in results) / len(results)
        print("\n=== Statistics ===")
        print(f"Total unique encodings: {len(results)}")
        print(f"Average length: {avg_len:.1f} chars")
        print(f"Min length: {min(len(r) for r in results)} chars")
        print(f"Max length: {max(len(r) for r in results)} chars")

        print("\n=== Sample (first 5) ===")
        for i, r in enumerate(sorted(results)[:5]):
            print(f"{i+1}: {r[:100]}{'...' if len(r)>100 else ''}")

if __name__ == "__main__":
    main()