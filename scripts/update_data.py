def fetch_vix_from_fred(days=220):
    # FRED 제공 CSV (키 필요 없음)
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    rows = r.text.strip().splitlines()
    data = []
    for line in rows[1:]:
        d, v = line.split(",")
        v = v.strip()

        # ✅ 빈값/결측값 처리
        if not v or v == ".":
            continue

        try:
            data.append({"date": d, "close": float(v)})
        except ValueError:
            # 혹시 모를 이상값도 스킵
            continue

    return data[-days:]
