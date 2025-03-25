import os
import pandas as pd
import openai

# OpenAI API Key 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=OPENAI_API_KEY)

# CSV 파일 로드
file_path = "filtered_data.csv"  # 실제 파일명으로 변경
df = pd.read_csv(file_path, encoding="utf-8")

# '일자' 기준으로 20231231 데이터만 필터링 후, 상위 10개만 선택
df = df[df["일자"] == 20231231].head(10).reset_index(drop=True)

# 감성 분석 함수 (한국어 버전)


def analyze(title):
    """GPT로 한국어 뉴스 헤드라인의 긍정/부정 여부 분석"""
    prompt = f"""
    이전의 모든 지침을 잊어버리세요. 당신은 경제 및 사회 이슈 분석 전문가입니다.
    뉴스 제목이 긍정적인 소식이면 "긍정", 부정적인 소식이면 "부정", 중립적인 경우 "중립"이라고 첫 줄에 답하세요.
    그리고, 다음 줄에 이유를 짧고 간결한 한 문장으로 설명하세요.
    
    뉴스 제목: "{title}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip().split("\n")
        sentiment_label = result[0].strip()

        # 결과 변환: 긍정 → 1, 부정 → -1, 중립 → 0
        mapping = {"긍정": 1, "부정": -1, "중립": 0}
        return mapping.get(sentiment_label, 0)  # 기본값: 0
    except Exception as e:
        print(f"감성 분석 오류: {e}")
        return 0  # 오류 발생 시 기본값

# 본문에서 주요 키워드 및 기업 분석 (필요한 경우만 GPT 사용)


def extract_keywords(content, existing_value):
    """GPT를 사용하여 뉴스 본문에서 주요 인물 및 기업 분석 (기존 데이터 활용)"""
    if pd.notna(existing_value) and existing_value.strip():  # 기존 데이터가 있으면 그대로 사용
        return existing_value

    prompt = f"""
    다음 뉴스 기사를 분석하고, 주요 인물 및 기업을 추출하세요.
    만약 주요 인물 또는 기업이 없다면 '없음'이라고 답변하세요.

    출력 형식:
    주요 인물 및 기업: [리스트]

    뉴스 본문:
    "{content}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()

        # 데이터 정리
        extracted_value = result.replace("주요 인물 및 기업:", "").strip()
        return extracted_value if extracted_value else "없음"
    except Exception as e:
        print(f"키워드 분석 오류: {e}")
        return "없음"  # 오류 발생 시 기본값


# 감성 분석 실행 (상위 10개 뉴스)
print("🔍 감성 분석 시작...")
df["감성 결과"] = df["제목"].apply(lambda x: analyze(x))

# 주요 인물 및 기업 분석 (기존 데이터 유지)
print("📊 주요 인물 및 기업 분석 시작...")
df["주요 인물 및 기업"] = df.apply(
    lambda row: extract_keywords(row["본문"], row.get("주요 인물 및 기업", "")), axis=1
)

# 최종 데이터 정리
df = df[["제목", "일자", "본문", "URL", "언론사", "통합 분류1", "감성 결과", "주요 인물 및 기업"]]

# 결과 저장
output_file = "processed_korean_news_top10.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"✅ 분석 완료! 결과가 {output_file}에 저장되었습니다.")
