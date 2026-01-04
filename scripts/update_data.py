import os
import json
import datetime
import requests

OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_vix_from_fred(days=220):
    # FRED 제공 CSV (키 필요 없음)
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    rows = r.text.strip().splitlines()
    data = []
    for line in rows[1:]:
        parts = line.split(",")
        if len(parts) < 2:
            continue
        d, v = parts[0], parts[1].strip()

        # 빈값/결측값 처리
        if not v or v == ".":
            continue

        try:
            data.append({"date": d, "close": float(v)})
        except ValueError:
            continue

    return data[-days:]

def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

def main():
    vix = fetch_vix_from_fred()
    print("VIX rows:", len(vix))

    payload = {
        "symbol": "VIXCLS",
        "updated": datetime.datetime.utcnow().isoformat() + "Z",
        "series": vix
    }

    out_path = os.path.join(OUT_DIR, "vix.json")
    write_json(out_path, payload)
    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
