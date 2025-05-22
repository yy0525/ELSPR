from openai import OpenAI
def chat_completion_openai_aliyun_api(system_prompt, user_prompt):
    client = OpenAI(api_key="", base_url="")
    completion = client.chat.completions.create(
        model="qwen-max",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return completion.choices[0].message.content
