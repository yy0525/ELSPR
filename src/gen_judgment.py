import sys
import os
import json
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from utils.get_api_answer import chat_completion_openai_aliyun_api

lock = threading.Lock()
processed_count = 0

def run_judgment_and_log(prompt, question, model_a, model_b, output_file="judgments.jsonl", max_retries=10):
    global processed_count
    for attempt in range(1, max_retries + 1):
        try:
            judgment = chat_completion_openai_aliyun_api(prompt)
            record = {
                "question": question,
                "model_a": model_a,
                "model_b": model_b,
                "prompt": prompt,
                "judgment": judgment
            }
            with lock:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            with lock:
                processed_count += 1
                print(f"[Success] Question '{question}' judged after {attempt} attempts.")
            return True
        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Error: {str(e)}")
            if attempt == max_retries:
                with lock:
                    processed_count += 1
                    print(f"[Failed] Question '{question}' failed after {attempt} attempts.")
                return False


def process_model(model_name, args):
    input_dir = os.path.join(args.folder_path, model_name)
    output_dir = os.path.join(args.output_root, model_name)

    if not os.path.exists(input_dir):
        print(f"Model directory {input_dir} does not exist. Skipping...")
        return

    os.makedirs(output_dir, exist_ok=True)

    datasets = args.dataset if args.dataset else [d for d in os.listdir(input_dir) if d.endswith(".json")]

    for dataset in datasets:
        input_file = os.path.join(input_dir, dataset)
        output_file = os.path.join(output_dir, dataset)

        if not os.path.exists(input_file):
            print(f"Input file {input_file} does not exist. Skipping...")
            continue

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to load {input_file}: {e}")
            continue

        questions = data.get("questions", []) if isinstance(data, dict) else []

        with ThreadPoolExecutor(max_workers=args.max_threads) as executor:
            futures = []
            for idx, item in enumerate(questions):
                question = item.get("question", "")
                model_a_response = item.get("model_a_response", "")
                model_b_response = item.get("model_b_response", "")

                prompt = build_prompt(question, model_a_response, model_b_response)

                futures.append(
                    executor.submit(run_judgment_and_log, prompt, question, model_a_response, model_b_response, output_file)
                )

            for future in as_completed(futures):
                future.result()

def build_prompt(template_type,instruction, output_1, output_2):
    """
    构造 prompt，用于对比两个模型的回答质量。
    返回一个符合新模板结构的 prompt。
    """
    if template_type == "cot":
        template = """I require a leaderboard for various large language models. I'll provide you with prompts given to these models and their corresponding outputs. Your task is to assess these responses, and select the model that produces the best output from a human perspective.

## Instruction

{{
    "instruction": "{instruction}",
}}

## Model Outputs

Here are the unordered outputs from the models. Each output is associated with a specific model, identified by a unique model identifier.

[
    {{
        "model_identifier": "m",
        "output": "{output_1}"
    }},
    {{
        "model_identifier": "M",
        "output": "{output_2}"
    }}
]

## Task

Evaluate the models based on the quality and relevance of their outputs, and select the model that generated the best output. Answer by first providing a concise explanation and then end your answer by providing the model identifier of the best output. We will use the last character of your output `output[-1]` as the name of the best model, so make sure you finish with the token of the model identifiers and nothing else: `m` or `M` (no quotes, no dots, no backticks, no new lines, ...). For example:

### Concise explanation
...some text...

### Which is best, m or M?
M

Now is your turn.

## Your answer: "Concise explanation" followed by "Which is best, m or M?"
"""
    else:
        template ="""I require a leaderboard for various large language models. I'll provide you with prompts given to these models and their corresponding outputs. Your task is to assess these responses, and select the model that produces the best output from a human perspective. If you determine that both outputs are of equal quality or are unable to decide which one is better, you should indicate a tie by providing the identifier `D`.

## Instruction

{{
    "instruction": "{instruction}",
}}

## Model Outputs

Here are the unordered outputs from the models. Each output is associated with a specific model, identified by a unique model identifier.

{{
    {{
        "model_identifier": "m",
        "output": "{output_1}"
    }},
    {{
        "model_identifier": "M",
        "output": "{output_2}"
    }}
}}

## Task

Evaluate the models based on the quality and relevance of their outputs, and select the model that generated the best output. Answer by first providing a concise explanation and then end your answer by providing the model identifier of the best output. If you determine that both outputs are of equal quality or cannot decide which one is better, indicate a tie by using the identifier `D`. We will use the last character of your output `output[-1]` as the name of the best model, so make sure you finish with the token of the model identifiers and nothing else: `m`, `M`  or `D` (no quotes, no dots, no backticks, no new lines, ...). For example:

### Concise explanation
...some text...

### Which is best, m, M or D?
M

Now is your turn.

## Your answer: "Concise explanation" followed by "Which is best, m, M or D?"
"""

    return template.format(
        instruction=instruction,
        output_1=output_1,
        output_2=output_2
    )



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split model results into dataset-specific JSON files.")
    parser.add_argument(
        "--model-name",
        type=str,
        nargs='+',
        default=None,
        help="Specific model name(s) to process (e.g., airoboros-33b). Default: all models in folder_path."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        nargs='+',
        default=None,
        help="Specific dataset name(s) to generate (e.g., helpful_base). Default: all datasets."
    )
    parser.add_argument(
        "--prompt-template",
        type=str,
        nargs='+',
        default="cot",
        help="Specific prompt-template type. Default: cot."
    )
    parser.add_argument(
        "--folder-path",
        type=str,
        default="../data/selected_models",
        help="Path to the root folder containing model directories. Default: ../model_results"
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="../data/datasets",
        help="Root path for output files. Default: ../data/selected_models"
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=5,
        help="Maximum number of threads to use for parallel processing. Default: 5"
    )

    args = parser.parse_args()

    if args.model_name:
        model_names = args.model_name
    else:
        model_names = [d for d in os.listdir(args.folder_path) if os.path.isdir(os.path.join(args.folder_path, d))]

    with ThreadPoolExecutor(max_workers=args.max_threads) as pool:
        pool.map(lambda model: process_model(model, args), model_names)

    print(f"Total processed questions: {processed_count}")
