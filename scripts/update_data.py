import os, json, datetime, requests

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_vix(days=220):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    rows = r.text.strip().splitlines()

    out = []
    for line in rows[1:]:
        parts = line.split(",")
        if len(parts) < 2: 
            continue
        d, v = parts[0], parts[1].strip()
        if not v or v == ".":
            continue
        try:
            out.append({"date": d, "close": float(v)})
        except:
            continue
    return out[-days:]


def fetch_kospi(days=220):
    # ✅ 네가 받은 서비스의 endpoint 기반
    # Endpoint: https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService
    # 호출 메서드: /getStockMarketIndex (문서에 있음)
    key = os.getenv("DATA_GO_KR_SERVICE_KEY")
    if not key:
        raise RuntimeError("Missing secret env: DATA_GO_KR_SERVICE_KEY")

    base = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

    # idxNm 표기가 케이스마다 달라서 후보를 돌림
    candidates = ["KOSPI", "코스피", "코스피 종합", "코스피지수"]

    last_error = None
    for idxNm in candidates:
        try:
            params = {
                "serviceKey": key,
                "resultType": "json",
                "numOfRows": "2000",
                "pageNo": "1",
                "idxNm": idxNm
            }
            r = requests.get(base, params=params, timeout=30)
            r.raise_for_status()
            j = r.json()

            items = (
                j.get("response", {})
                 .get("body", {})
                 .get("items", {})
                 .get("item", [])
            )
            if not items:
                continue
            if not isinstance(items, list):
                items = [items]

            out = []
            for it in items:
                basDt = it.get("basDt")
                clpr = it.get("clpr")
                if not basDt or clpr in (None, ""):
                    continue
                try:
                    d = f"{basDt[:4]}-{basDt[4:6]}-{basDt[6:8]}"
                    out.append({"date": d, "close": float(str(clpr).replace(",", ""))})
                except:
                    continue

            if out:
                out.sort(key=lambda x: x["date"])
                return out[-days:]

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"KOSPI fetch failed: {last_error}")


def write(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    vix = fetch_vix()
    kospi = fetch_kospi()

    write(os.path.join(DATA_DIR, "vix.json"), {"symbol":"VIXCLS", "updated": datetime.datetime.utcnow().isoformat()+"Z", "series": vix})
    write(os.path.join(DATA_DIR, "kospi.json"), {"symbol":"KOSPI", "updated": datetime.datetime.utcnow().isoformat()+"Z", "series": kospi})

    print("OK. vix:", len(vix), "kospi:", len(kospi))

if __name__ == "__main__":
    main()
