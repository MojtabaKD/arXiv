import urllib.request
import argparse
import time
import json
import re
import os
import socket
import shutil
import random

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

parser = argparse.ArgumentParser()
parser.add_argument('skip', type=int, default=0, nargs='?')
args = parser.parse_args()
skp_arg = args.skip


def download(file_name, arxivid):
    if os.path.exists(file_name):
        print("-", end="")
        return

    url = f"https://export.arxiv.org/pdf/{arxivid}"

    max_retries = 10
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "arXiv downloader (personal research)"
                }
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                with open(file_name, "wb") as out:
                    shutil.copyfileobj(response, out)

            print(f"{file_name} ---> downloaded.")

            # Be polite to arXiv
            time.sleep(random.uniform(3, 6))
            return

        except urllib.error.HTTPError as e:

            if e.code == 429:
                wait = retry_delay * (attempt + 1)
                print(
                    f"429 rate limit for {arxivid}, "
                    f"retrying in {wait}s..."
                )
                time.sleep(wait)
                continue

            print(f"HTTP Error {e.code} for {arxivid}")
            return

        except Exception as e:
            print(f"Error downloading {arxivid}: {e}")
            return

    print(f"FAILED after {max_retries} retries: {arxivid}")

math_subs_set = set(subs["math"])
phys_subs_set = set(
    subs["physics"]
    + subs["astro-ph"]
    + ["astro-ph"]
    + subs["cond-mat"]
    + subs["nlin"]
    + subs["high_energy"]
)

skp = 0

with open('../arxiv-metadata-oai-snapshot.json', 'r') as metadatafile:
    for line in metadatafile:
        try:
            if (skp >= skp_arg):
                js = json.loads(line)
                
                id       = js['id']
                cats     = js['categories']
                cats_set = set(cats.split())
                
                # print(categories)
                
                if (phys_subs_set & cats_set):
                    id_nrm = re.sub('/', '-', id)
                    download('/media/mojusr/Huge/Books/Journals/arXiv/pdf/'+id_nrm+'.pdf', id)
                else:
                    print(f'not phys--->{id}')
            else:
                skp += 1
        except Exception as e:
            print(f'error was this -->{e}')
            time.sleep(5)
