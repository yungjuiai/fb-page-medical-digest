import json
import os

from groq import Groq

MODEL = "llama-3.3-70b-versatile"

PROMPT_TEMPLATE = """你是一個粉絲專頁貼文篩選助手。以下是「達叔礙唬爛」這個醫療粉絲專頁的一篇貼文原文。

請判斷這篇貼文是否與「醫療或治療」相關（例如：疾病衛教、用藥治療、臨床照護知識、醫學新知、健康衛教），
而不是純粹的活動宣傳、招募、閒聊、廣告或行政公告。

如果相關，請用繁體中文整理 2-4 條重點摘要（條列式，簡潔）。
如果不相關，summary 留空字串即可。

請只回傳 JSON，格式如下，不要有其他文字：
{{"is_medical_treatment": true/false, "summary": "- 重點1\\n- 重點2"}}

貼文原文：
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
