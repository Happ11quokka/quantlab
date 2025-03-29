import json
import os
import openai
from pykrx import stock

# 환경 변수에서 OPENAI_API_KEY를 가져옵니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

client = openai.Client(api_key=OPENAI_API_KEY)


def resolve_official_name(company: str) -> str:
    """
    입력된 회사명(company)에 대해 아래 조건을 만족하는 한 줄짜리 응답을 반환합니다.
      1. 회사명이 한국거래소(KRX)에 상장되어 있는지 확인합니다.
      2. 상장되어 있다면 공식 상장법인명을 정확히 한글로 반환합니다.
         (예: 입력이 "우리은행"일 경우, 실제 상장법인명은 "우리금융지주"일 수 있습니다.)
      3. 상장되어 있지 않거나 확인할 수 없으면 "Not Listed"만 반환합니다.
    """
    prompt = f"""
회사명: "{company}"

아래 조건을 만족하는 응답을 작성해 주세요.

1. 입력된 회사명이 한국거래소(KRX)에 상장된 회사인지 확인합니다.
2. 만약 상장되어 있다면, 해당 회사의 공식 상장법인명을 정확히 한글로만 반환해 주세요.
   (예를 들어, 입력값이 "우리은행"일 경우, 실제 상장 법인명은 "우리금융지주"일 수 있습니다.)
3. 만약 상장되어 있지 않거나, 상장 여부를 확인할 수 없는 경우에는 단순히 "Not Listed"만 반환해 주세요.
4. 응답은 오직 결과값(공식 상장법인명 또는 "Not Listed")만 한 줄로 출력해 주세요.
"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content.strip().strip('"')


# 입력 JSON 파일 경로 (예시: "second_summary.json"이 시간대별 데이터를 담고 있다고 가정)
input_file = "/Users/imdonghyeon/quantlab/results/second_summary.json"
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 데이터 구조는 예시와 같이 {"장전": [...], "장중": [...], "장후": [...]} 형태라고 가정합니다.
# pykrx를 이용해 KRX에 상장된 모든 회사의 공식 상장법인명과 티커를 딕셔너리로 생성합니다.
krx = {}
for market in ("KOSPI", "KOSDAQ"):
    for ticker in stock.get_market_ticker_list(market=market):
        name = stock.get_market_ticker_name(ticker)
        krx[name] = ticker


def get_code(official_name: str) -> str:
    """
    공식 상장법인명(official_name)이 krx 딕셔너리에 있다면 해당 티커를 반환하고,
    없으면 fuzzy matching을 통해서 검색합니다.
    """
    if official_name == "Not Listed":
        return "Not Listed"
    if official_name in krx:
        return krx[official_name]
    # 이름이 정확하게 매칭되지 않을 경우, 부분 매칭을 시도합니다.
    for name, code in krx.items():
        if official_name in name or name in official_name:
            return code
    return "Not Listed"


# 각 시간대별(예: "장전", "장중", "장후") 레코드에 대해 처리합니다.
for period in data:
    records = data[period]
    for record in records:
        company = record.get("Company", "").strip()
        if company:
            # GPT-4를 이용해 공식 상장법인명으로 변환
            official_name = resolve_official_name(company)
            record["Official_Company"] = official_name
            # 공식 상장법인명을 이용하여 pykrx 종목코드 조회
            record["Stock_Code"] = get_code(official_name)
        else:
            record["Official_Company"] = ""
            record["Stock_Code"] = ""

# 결과를 출력 파일로 저장합니다.
output_file = "/Users/imdonghyeon/quantlab/results/final_withStockcodes.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"업데이트 완료: 변환된 데이터가 {output_file}에 저장되었습니다.")
