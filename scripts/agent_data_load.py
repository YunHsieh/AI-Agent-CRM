import json
import pathlib
import pandas as pd

conversation_path = pathlib.Path("dummy_data/all_conversations.json")

result = []
for _obj in json.load(conversation_path.open()):
    tmp = {
        'question': _obj[0]['content'][0]['text'],
        'expected_answer': '',
        'my_answer': '',
        'using_agent': '',
        'achievement_rate': ''
    }

    if len(_obj) > 1:
        tmp['expected_answer'] = _obj[1]['content'][0]['text']
    result.append(tmp)

pd.DataFrame(result).to_csv('dummy_data/test_data.csv', index=False)
