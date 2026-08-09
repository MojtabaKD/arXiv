import urllib.request
import argparse
import time
import json
import re
import os
import shutil
import random
import hashlib

# ---------- Configuration ----------
BASE_DIR = "/media/mojusr/Huge/Books/Journals/arXiv/pdf"
BLACKLIST_FILE = os.path.join(BASE_DIR, "404_blacklist.txt")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
# ------------------------------------

# Ensure tmp directory exists
os.makedirs(TMP_DIR, exist_ok=True)

subs = {
    "cs": [
        "cs.AI", "cs.AR", "cs.CC", "cs.CE", "cs.CG", "cs.CL", "cs.CR", "cs.CV",
        "cs.CY", "cs.DB", "cs.DC", "cs.DL", "cs.DM", "cs.DS", "cs.ET", "cs.FL",
        "cs.GL", "cs.GR", "cs.GT", "cs.HC", "cs.IR", "cs.IT", "cs.LG", "cs.LO",
        "cs.MA", "cs.MM", "cs.MS", "cs.NA", "cs.NE", "cs.NI", "cs.OH", "cs.OS",
        "cs.PF", "cs.PL", "cs.RO", "cs.SC", "cs.SD", "cs.SE", "cs.SI", "cs.SY"
    ],
    "econ": [
        "econ.EM", "econ.GN", "econ.TH"
    ],
    "eess": [
        "eess.AS", "eess.IV", "eess.SP", "eess.SY"
    ],
    "math": [
        "math.AC", "math.AG", "math.AP", "math.AT",
        "math.CA", "math.CO", "math.CT", "math.CV",
        "math.DG", "math.DS", "math.FA", "math.GM",
        "math.GN", "math.GR", "math.GT", "math.HO",
        "math.IT", "math.KT", "math.LO", "math.MG",
        "math.MP", "math.NA", "math.NT", "math.OA",
        "math.OC", "math.PR", "math.QA", "math.RA",
        "math.RT", "math.SG", "math.SP", "math.ST"
    ],
    "astro-ph": [
        "astro-ph.CO", "astro-ph.EP", "astro-ph.GA",
        "astro-ph.HE", "astro-ph.IM", "astro-ph.SR"
    ],
    "cond-mat": [
        "cond-mat.dis-nn", "cond-mat.mes-hall", "cond-mat.mtrl-sci",
        "cond-mat.other", "cond-mat.quant-gas", "cond-mat.soft",
        "cond-mat.stat-mech", "cond-mat.str-el", "cond-mat.supr-con"
    ],
    "nlin": [
        "nlin.AO", "nlin.CD", "nlin.CG", "nlin.PS", "nlin.SI"
    ],
    "physics": [
        "physics.acc-ph", "physics.ao-ph", "physics.app-ph",
        "physics.atm-clus", "physics.atom-ph", "physics.bio-ph",
        "physics.chem-ph", "physics.class-ph", "physics.comp-ph",
        "physics.data-an", "physics.ed-ph", "physics.flu-dyn",
        "physics.gen-ph", "physics.geo-ph", "physics.hist-ph",
        "physics.ins-det", "physics.med-ph", "physics.optics",
        "physics.plasm-ph", "physics.pop-ph", "physics.soc-ph",
        "physics.space-ph"
    ],
    "q-bio": [
        "q-bio.BM", "q-bio.CB", "q-bio.GN", "q-bio.MN", "q-bio.NC",
        "q-bio.OT", "q-bio.PE", "q-bio.QM", "q-bio.SC", "q-bio.TO"
    ],
    "q-fin": [
        "q-fin.CP", "q-fin.EC", "q-fin.GN", "q-fin.MF",
        "q-fin.PM", "q-fin.PR", "q-fin.RM", "q-fin.ST", "q-fin.TR"
    ],
    "stat": [
        "stat.AP", "stat.CO", "stat.ME",
        "stat.ML", "stat.OT", "stat.TH"
    ],
    "high_energy": [
        "gr-qc",
        "hep-ex",
        "hep-lat",
        "hep-ph",
        "hep-th",
        "math-ph",
        "nucl-ex",
        "nucl-th",
        "quant-ph"
    ]
}

math_subs_set = set(subs["math"])
phys_subs_set = set(
    subs["physics"]
    + subs["astro-ph"]
    + ["astro-ph"]
    + subs["cond-mat"]
    + subs["nlin"]
    + subs["high_energy"]
)

# ---------- Build filename cache ----------
print("Building cache of existing PDF files...")
existing_filenames = set()
for root, dirs, files in os.walk(BASE_DIR):
    if root == TMP_DIR:
        continue
    for f in files:
        if f.lower().endswith('.pdf'):
            existing_filenames.add(f)
print(f"Found {len(existing_filenames)} existing PDF files.")
# ------------------------------------------

# ---------- Load 404 blacklist ----------
print("Loading 404 blacklist...")
if os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, 'r') as f:
        blacklist = set(line.strip() for line in f if line.strip())
else:
    blacklist = set()
print(f"Loaded {len(blacklist)} blacklisted IDs.")
# ------------------------------------------

def build_hash_path(md5_hash):
    """
    Three‑level nested path:
      - first character
      - first two characters
      - first three characters
    Example: md5_hash = "f818d3..." -> "/f/f8/f81/"
    """
    if not md5_hash:
        return "/_/__/___/"
    first_char = md5_hash[0]
    first_two = md5_hash[:2] if len(md5_hash) >= 2 else "__"
    first_three = md5_hash[:3] if len(md5_hash) >= 3 else "___"
    return f"/{first_char}/{first_two}/{first_three}/"

def compute_md5(file_path):
    """Compute MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_and_place(arxiv_id, filename):
    """
    Download PDF for arxiv_id and move it into the hash-based structure.
    Returns True on success, False on failure.
    """
    url = f"https://export.arxiv.org/pdf/{arxiv_id}"
    tmp_path = os.path.join(TMP_DIR, filename)

    max_retries = 10
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "arXiv downloader (personal research)"}
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(tmp_path, "wb") as out:
                    shutil.copyfileobj(response, out)

            md5_hash = compute_md5(tmp_path)

            # Build destination directory using three‑level nesting
            dest_subdir = build_hash_path(md5_hash)
            dest_dir = BASE_DIR + dest_subdir
            os.makedirs(dest_dir, exist_ok=True)

            dest_file = os.path.join(dest_dir, filename)

            if os.path.exists(dest_file):
                print(f"File already exists at {dest_file}. Skipping move.")
                os.remove(tmp_path)
                return True

            shutil.move(tmp_path, dest_file)
            print(f"Downloaded and moved: {dest_file}")

            existing_filenames.add(filename)

            time.sleep(random.uniform(5, 7))
            return True

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = retry_delay * (attempt + 1)
                print(f"429 rate limit for {arxiv_id}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            elif e.code == 404:
                print(f"⚠️  404 Not Found for {arxiv_id} — adding to blacklist.")
                with open(BLACKLIST_FILE, 'a') as f:
                    f.write(f"{arxiv_id}\n")
                blacklist.add(arxiv_id)
                return False
            print(f"HTTP Error {e.code} for {arxiv_id}")
            return False
        except Exception as e:
            print(f"Error downloading {arxiv_id}: {e}")
            return False

    print(f"FAILED after {max_retries} retries: {arxiv_id}")
    return False

# ---------- Main loop ----------
parser = argparse.ArgumentParser()
parser.add_argument('skip', type=int, default=0, nargs='?')
args = parser.parse_args()
skp_arg = args.skip

skp = 0
with open('../arxiv-metadata-oai-snapshot.json', 'r') as metadatafile:
    for line in metadatafile:
        try:
            if skp >= skp_arg:
                js = json.loads(line)
                arxiv_id = js['id']
                if arxiv_id in blacklist:
                    print(f"⏭️  Known 404 (skipping): {arxiv_id}")
                    continue
                cats = js['categories']
                cats_set = set(cats.split())

                if math_subs_set & cats_set:
                    id_nrm = re.sub('/', '-', arxiv_id)
                    filename = id_nrm + '.pdf'

                    if filename in existing_filenames:
                        print(f"✅ Already exists: {filename}")
                    else:
                        print(f"⬇️  Downloading: {arxiv_id}")
                        success = download_and_place(arxiv_id, filename)
                        if not success:
                            print(f"❌ Failed to download {arxiv_id}")
                else:
                    print(f"⏭️  Not related: {arxiv_id}")
            else:
                skp += 1
        except Exception as e:
            print(f"Error processing line: {e}")
