import pandas as pd

# CSV 파일 로드 (파일명을 적절히 변경)
file_path = "korean_data_selected.csv"

# CSV 파일 읽기 (UTF-8 인코딩, 필요시 다른 인코딩 사용)
df = pd.read_csv(file_path, encoding="utf-8")

# '일자' 열이 20231231인 데이터만 필터링
filtered_df = df[df['일자'] == 20231231]

# 필터링된 데이터 저장 (필요시 경로 변경)
filtered_file_path = "filtered_data.csv"
filtered_df.to_csv(filtered_file_path, index=False, encoding="utf-8")

print(f"Filtered data saved to {filtered_file_path}")
