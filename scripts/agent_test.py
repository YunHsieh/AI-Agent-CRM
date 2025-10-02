import pathlib

import pydantic
import requests
import pandas as pd
from pydantic import Field
from pydantic_ai import Agent

from intentions.router import IntentionRouter


class CheckerModel(pydantic.BaseModel):
    rate: int = Field(..., description="差異程度 1~100")
    reason: str = Field(..., description="精準說明差異的原因")


checker_agent = Agent(
    "openai:gpt-4.1-mini",
    system_prompt=f"""你是一個 AI 測試兼客服專家，你將會幫我判斷兩段句子語意符合度
會提供 0~100% 精確比率
""",
    output_type=CheckerModel,
)


async def sentence_checker(expected_sentence: str, output_sentence: str) -> str:
    prompt = f"""
experted sentence: {expected_sentence}
output sentence: {output_sentence}
"""
    llm_result = await checker_agent.run(prompt)
    return llm_result.output

async def main():
    data_path = pathlib.Path("dummy_data/updated_test_data.csv")
    df = pd.read_csv(data_path, dtype=str, keep_default_na=False)
    router = IntentionRouter()
    try:
        for idx, row in df[::-1].iterrows():
            result = router.find_best_agent(row['question'])
            max_key = max(result, key=result.get)
            df.loc[idx, 'using_agent'] = max_key
            if pd.isnull(row['my_answer']) or row['my_answer'] != '':
                continue
            print(row)
            response = requests.post(
                'http://localhost:8000/chat',
                json={
                    "message": row['question'],
                }
            )
            df.loc[idx, 'my_answer'] = response.json()['result']
            llm_result = await sentence_checker(row['expected_answer'], response.json()['result'])
            print(llm_result)
            df.loc[idx, 'achievement_rate'] = llm_result.rate
            df.loc[idx, 'description'] = llm_result.reason
            # if llm_result.rate < 80:
            #     break
            if row['expected_answer'] == '':
                break
    except Exception as e:
        raise e
    finally:
        df.to_csv('dummy_data/updated_test_data.csv', index=False)

async def test():
    llm_result = await sentence_checker(
        "貨物今天會送達您家", "貨物已經出貨並會準確送到您家")
    return llm_result

if __name__ == "__main__":
    import asyncio
    # asyncio.run(test())
    asyncio.run(main())
