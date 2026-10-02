import os
import sys

from app.ingest import ingest


def main(folder: str):
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".pdf"):
            continue
        parts = os.path.splitext(fn)[0].split("_")
        if len(parts) < 3 or not parts[-1].isdigit():
            print(f"skip {fn} (expected <company>_<doctype>_<year>.pdf)")
            continue
        company, year = parts[0], int(parts[-1])
        doc_type = "_".join(parts[1:-1])
        n = ingest(os.path.join(folder, fn), company, doc_type, year)
        print(f"{fn}: {n} chunks")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")