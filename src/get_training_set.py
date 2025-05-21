import json
from json import JSONDecodeError


def get_training_set(original_path, answer_path, dataset_name):
    answer_dict = {}
    with open(answer_path, "r") as f:
        for line in f:
            data = json.loads(line)
            qid = data["question_id"]
            m1 = data["model1"]
            m2 = data["model2"]
            winner = data["winner"]

            sorted_models = sorted([m1, m2])
            key = (qid, sorted_models[0], sorted_models[1])
            if winner == "tie":
                winner_model = "tie"
            else:
                winner_model = data[winner]
            answer_dict[key] = winner_model
    with open(original_path, "r", encoding="utf-8") as f_result:
        right_data = []
        wrong_data = []
        all_data = []
        for line in f_result:
            try:
                data = json.loads(line)
                qid = data["question_id"]
                m1 = data["model1"]
                m2 = data["model2"]
                system_prompt = "You are a highly efficient assistant, who evaluates and selects the best large language model (LLMs) based on the quality of their responses to a given instruction. This process will be used to create a leaderboard reflecting the most accurate and human-preferred answers."
                sorted_models = sorted[m1, m2]
                key = (qid, sorted_models[0], sorted_models[1])
                answer = answer_dict[key]
                if data["g1_winner"] == "tie":
                    g1_winner = "tie"
                elif data["g1_winner"] == "error":
                    g1_winner = "error"
                else:
                    g1_winner = data[data["g1_winner"]]
                if g1_winner == answer:
                    right_item = {
                        "instruction": data["g1_user_prompt"],
                        "input": "",
                        "output": data["g1_judgement"],
                        "system_prompt": system_prompt,
                    }
                    right_data.append(right_item)
                else:
                    wrong_item = {
                        "instruction": data["g1_user_prompt"],
                        "input": "",
                        "output": data["g1_judgement"],
                        "system_prompt": system_prompt,
                    }
                    wrong_data.append(wrong_item)
                if data["g2_winner"] == "tie":
                    g2_winner = "tie"
                elif data["g2_winner"] == "error":
                    g2_winner = "error"
                else:
                    g2_winner = data[data["g2_winner"]]
                if g2_winner == answer:
                    right_item = {
                        "instruction": data["g2_user_prompt"],
                        "input": "",
                        "output": data["g2_judgement"],
                        "system_prompt": system_prompt,
                    }
                    right_data.append(right_item)
                else:
                    wrong_item = {
                        "instruction": data["g2_user_prompt"],
                        "input": "",
                        "output": data["g2_judgement"],
                        "system_prompt": system_prompt,
                    }
                    wrong_data.append(wrong_item)
            except JSONDecodeError as e:
                print("josn decode error")
            all_data.extend(right_data)
            all_data.extend(wrong_data)
    with open(
        f"../../{dataset_name}/cleaned_traing_set_alpaca.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(right_data, f, ensure_ascii=False, indent=4)
        print(f"right:{len(right_data)}")
    with open(
        f"../../{dataset_name}/raw_traing_set_alpaca.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"right:{len(right_data)}")
