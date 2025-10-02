import pathlib
import requests
import pandas as pd
from pydantic_ai import Agent

from intentions.router import IntentionRouter


checker_agent = Agent(
    "openai:gpt-4.1-mini",
    system_prompt=f"""你是一個 AI 測試專家，你將會幫我判斷兩段句子結果符合度
會提供 0~100% 精確的浮點數
""",
)


async def sentence_checker(expected_sentence: str, output_sentence: str) -> str:
    prompt = f"""
experted sentence: {expected_sentence}
output sentence: {output_sentence}
"""
    llm_result = await checker_agent.run(prompt)
    return llm_result.output

async def main():
    data_path = pathlib.Path("dummy_data/test_data.csv")
    df = pd.read_csv(data_path, dtype=str, keep_default_na=False)
    router = IntentionRouter()

    for idx, row in df[::-1].iterrows():
        result = router.find_best_agent(row['question'])
        max_key = max(result, key=result.get)
        # Fixed: Use single .loc operation instead of chained indexing
        df.loc[idx, 'using_agent'] = max_key
        if pd.isnull(df.loc[idx, 'my_answer']):
            continue
        print(row['question'])
        response = requests.post(
            'http://localhost:8000/chat',
            json={
                "message": row['question'],
            }
        )
        print(response)
        df.loc[idx, 'my_answer'] = response.json()['result']
        llm_result = await sentence_checker(row['expected_answer'], response.json()['result'])
        llm_result = float(llm_result)
        print(llm_result)
        df.loc[idx, 'achievement_rate'] = llm_result
        if llm_result < 80:
            break
        if not pd.isnull(df.loc[idx, 'expected_answer']):
            break
        break
    df.to_csv('dummy_data/updated_test_data.csv', index=False)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
