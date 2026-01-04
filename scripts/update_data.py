import os, json, datetime
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
        d, v = line.split(",")
        if v == ".":
            continue
        data.append({"date": d, "close": float(v)})

    return data[-days:]

def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

def main():
    vix = fetch_vix_from_fred()
    write_json(
        f"{OUT_DIR}/vix.json",
        {"symbol": "VIXCLS", "updated": datetime.datetime.utcnow().isoformat() + "Z", "series": vix}
    )

if __name__ == "__main__":
    main()
