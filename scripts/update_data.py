import os
import json
import requests
from datetime import datetime

DATA_DIR = "data"

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def fetch_vix_from_fred(days=220):
    # FRED VIX (VIXCLS) - 일 1회 갱신(실시간 아님)
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    rows = r.text.strip().splitlines()
    data = []
    for line in rows[1:]:
        d, v = line.split(",")
        v = v.strip()
        if (not v) or v == ".":
            continue
        try:
            data.append({"date": d, "close": float(v)})
        except ValueError:
            continue

    return data[-days:]


def fetch_kospi_from_data_go_kr(days=220):
    """
    금융위원회_지수시세정보
    getStockMarketIndex 사용
    - 데이터는 실시간이 아니라 '영업일+1' 이후(대체로 오후 1시 이후) 반영되는 편
    """
    service_key = os.getenv("DATA_GO_KR_SERVICE_KEY")
    if not service_key:
        raise RuntimeError("Missing env var: DATA_GO_KR_SERVICE_KEY")

    base = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

    # idxNm은 환경/시점에 따라 표기가 달라질 수 있어서 후보를 여러 개 시도
    idx_candidates = ["KOSPI", "코스피", "코스피 종합", "코스피지수", "KOSPI 지수", "KOSPI종합"]

    last_err = None
    for idxNm in idx_candidates:
        try:
            params = {
                "serviceKey": service_key,   # Decoding 키를 그대로
                "resultType": "json",
                "numOfRows": "5000",
                "pageNo": "1",
                "idxNm": idxNm,
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

            out = []
            for it in items:
                basDt = it.get("basDt")
                clpr = it.get("clpr")
                if not basDt or clpr in (None, ""):
                    continue
                try:
                    # basDt: YYYYMMDD
                    d = f"{basDt[0:4]}-{basDt[4:6]}-{basDt[6:8]}"
                    out.append({"date": d, "close": float(clpr)})
                except Exception:
                    continue

            if not out:
                continue

            # 날짜 오름차순 정렬 후 최근 N개만
            out.sort(key=lambda x: x["date"])
            return out[-days:]

        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"KOSPI fetch failed. last error: {last_err}")


def write_json(filename, data):
    with open(os.path.join(DATA_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    ensure_dir()

    vix = fetch_vix_from_fred()
    kospi = fetch_kospi_from_data_go_kr()

    meta = {
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "note": "Some sources are not real-time. KOSPI is from data.go.kr (D+1 update typical)."
    }

    write_json("vix.json", vix)
    write_json("kospi.json", kospi)
    write_json("meta.json", meta)

    print("✅ data updated:", meta["updatedAt"])


if __name__ == "__main__":
    main()
