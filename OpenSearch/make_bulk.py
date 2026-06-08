import json

inp = "../arxiv-metadata-oai-snapshot.json"
out = "arxiv_bulk.json"

with open(inp) as f, open(out, "w") as w:
    for line in f:
        p = json.loads(line)

        doc = {
            "id": p.get("id"),
            "title": p.get("title"),
            "abstract": p.get("abstract"),
            "authors": p.get("authors"),
            "categories": p.get("categories"),
            "update_date": p.get("update_date")
        }

        w.write(json.dumps({"index": {"_index": "arxiv"}}) + "\n")
        w.write(json.dumps(doc) + "\n")
