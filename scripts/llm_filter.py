import json
import os

from groq import Groq

MODEL = "llama-3.3-70b-versatile"

PROMPT_TEMPLATE = """你是一個粉絲專頁貼文篩選助手。以下是「達叔礙唬爛」這個醫療粉絲專頁的一篇貼文，
因為 Facebook 限制，只能取得貼文開頭被截斷的預覽文字（可能在句子中間就結束）。

請根據這段有限的文字，盡力判斷這篇貼文的重點是否為「疾病或治療」本身的醫療知識
（例如：疾病成因與症狀、用藥與治療方式、臨床照護技巧、醫學新知、健康衛教）。

即使貼文發生在醫療場域（例如提到醫院、加護病房、病房、醫療人員），只要重點是下列這些「制度／
工具／數據」而非疾病或治療知識本身，都請判定為不相關：品質指標、資訊系統或電子化流程、行政管理、
教學或研究方法、活動宣傳、招募、閒聊、廣告、行政公告。

如果相關，請用繁體中文整理 1-3 條重點摘要（條列式，簡潔，根據現有文字合理推斷即可，不要編造細節）。
如果不相關，summary 留空字串即可。

請只回傳 JSON，格式如下，不要有其他文字：
{{"is_medical_treatment": true/false, "summary": "- 重點1\\n- 重點2"}}

貼文預覽文字：
{post_text}
"""


def classify_and_summarize(post_text, api_key=None):
    client = Groq(api_key=api_key or os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "user", "content": PROMPT_TEMPLATE.format(post_text=post_text)}
        ],
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    return bool(data.get("is_medical_treatment")), data.get("summary", "")
