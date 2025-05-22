import json
import argparse
import os
from json import JSONDecodeError


def load_answer_dict(answer_path):
    """
    Load the answer file (JSONL format) and build a dictionary mapping from question ID to winner.

    Args:
        answer_path (str): Path to the answer file (JSONL format)

    Returns:
        dict: key is (question_id, sorted_model1, sorted_model2), value is the winning model or 'tie'
    """
    answer_dict = {}
    with open(answer_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                qid = data["question_id"]
                m1 = data["model1"]
                m2 = data["model2"]
                winner = data["winner"]

                # Sort model names to ensure consistent key
                sorted_models = sorted([m1, m2])
                key = (qid, sorted_models[0], sorted_models[1])

                if winner == "tie":
                    answer_dict[key] = "tie"
                else:
                    answer_dict[key] = data[winner]
            except (KeyError, JSONDecodeError) as e:
                print(f"Skipping invalid line in answer file: {e}")
    return answer_dict


def process_original_file(original_path, answer_dict):
    """
    Process the original JSONL file and extract correct and incorrect judgment samples.

    Args:
        original_path (str): Path to the original JSONL file
        answer_dict (dict): Dictionary of correct answers used to determine correctness

    Returns:
        tuple: (right_data, wrong_data)
    """
    right_data = []
    wrong_data = []

    with open(original_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                qid = data["question_id"]
                m1 = data["model1"]
                m2 = data["model2"]
                system_prompt = data.get("system_prompt", "")

                sorted_models = sorted([m1, m2])
                key = (qid, sorted_models[0], sorted_models[1])

                if key not in answer_dict:
                    continue  # Skip if no corresponding answer exists

                answer = answer_dict[key]

                # Process g1 result
                g1_winner = data.get("g1_winner")
                if g1_winner == "tie":
                    g1 = "tie"
                elif g1_winner == "error":
                    g1 = "error"
                else:
                    g1 = data.get(g1_winner)

                item_g1 = {
                    "instruction": data["g1_user_prompt"],
                    "input": "",
                    "output": data["g1_judgement"],
                    "system_prompt": system_prompt,
                }

                if g1 == answer:
                    right_data.append(item_g1)
                else:
                    wrong_data.append(item_g1)

                # Process g2 result
                g2_winner = data.get("g2_winner")
                if g2_winner == "tie":
                    g2 = "tie"
                elif g2_winner == "error":
                    g2 = "error"
                else:
                    g2 = data.get(g2_winner)

                item_g2 = {
                    "instruction": data["g2_user_prompt"],
                    "input": "",
                    "output": data["g2_judgement"],
                    "system_prompt": system_prompt,
                }

                if g2 == answer:
                    right_data.append(item_g2)
                else:
                    wrong_data.append(item_g2)

            except JSONDecodeError as e:
                print(f"JSON decode error: {e}")
            except KeyError as e:
                print(f"Missing expected field in data: {e}")

    return right_data, wrong_data


def save_results(right_data, wrong_data, dataset_name):
    """
    Save results into JSON files.

    Args:
        right_data (list): List of correctly judged items
        wrong_data (list): List of incorrectly judged items
        dataset_name (str): Name of the dataset, used for output directory
    """
    all_data = right_data + wrong_data

    os.makedirs(f"../../{dataset_name}", exist_ok=True)

    with open(f"../../{dataset_name}/cleaned_traing_set_alpaca.json", "w", encoding="utf-8") as f:
        json.dump(right_data, f, ensure_ascii=False, indent=4)
        print(f"Saved cleaned dataset with {len(right_data)} items.")

    with open(f"../../{dataset_name}/raw_traing_set_alpaca.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"Saved raw dataset with {len(all_data)} items.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate training sets from judgment results.")

    parser.add_argument(
        "--original-path",
        type=str,
        required=True,
        help="Path to the original JSONL file containing judgments."
    )

    parser.add_argument(
        "--answer-path",
        type=str,
        required=True,
        help="Path to the JSONL file containing correct answers (winners)."
    )

    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="Name of the dataset used to determine output directory."
    )

    args = parser.parse_args()

    # Step 1: Load the answer dictionary
    answer_dict = load_answer_dict(args.answer_path)

    # Step 2: Process original file and separate into right/wrong samples
    right_data, wrong_data = process_original_file(args.original_path, answer_dict)

    # Step 3: Save results to disk
    save_results(right_data, wrong_data, args.dataset_name)