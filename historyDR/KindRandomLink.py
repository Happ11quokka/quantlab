import random
import pandas as pd

BASE_URL = "https://kind.krx.co.kr/common/disclsviewer.do?method=search&acptno=2024"


def generate_links(num_links=1000):
    generated_links = set()

    while len(generated_links) < num_links:
        # MMDD (랜덤 날짜)
        month_day = f"{random.randint(1, 12):02d}{random.randint(1, 31):02d}"
        random_number = f"{random.randint(1000, 9999)}"  # 4자리 랜덤 숫자
        full_url = f"{BASE_URL}{month_day}0{random_number}&docno=&viewerhost=&viewerport="
        generated_links.add(full_url)  # 중복 방지

    return list(generated_links)


# 1000개 링크 생성
links = generate_links(1000)

# CSV 저장
df = pd.DataFrame(links, columns=["Generated Links"])
df.to_csv("generated_links.csv", index=False, encoding="utf-8-sig")

print("✅ 1000개 링크 생성 완료! 'generated_links.csv' 파일로 저장되었습니다.")
