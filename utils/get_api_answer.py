from openai import OpenAI
# def chat_completion_openai_aliyun_api(system_prompt, user_prompt):
#     client = OpenAI(api_key="", base_url="")
#     completion = client.chat.completions.create(
#         model="qwen-max",
#         temperature=0,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ],
#     )
#     print(user_prompt)
#     return completion.choices[0].message.content
def chat_completion_openai_aliyun_api(system_prompt, user_prompt):


    try:
        client = OpenAI(
            api_key="sk-f486117f7c47494aa47fb8c1627492fc",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            model="qwen-max",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        print(user_prompt)
        return completion.choices[0].message.content
    except Exception as e:
        print(f"API error: {e}")
        return "error"
