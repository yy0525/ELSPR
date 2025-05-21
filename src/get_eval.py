import os.path
import pandas as pd

from utils.eval import get_eval_entropy,get_eval_non_tran

def get_eval_result(dataset_list,flag):
    file_paths = []
    for dataset_path in dataset_list:
        file_paths
    results = []
    for file_path in file_paths:
        if flag == 'non-trans':
            result = get_eval_non_tran(file_path)
        else: result = get_eval_entropy()
        model_name = os.path.basename(file_path).split(".")
        result["model_name"] = model_name
        results.append(result)
    df = pd.DataFrame(results)
    output_excel_path = f""
    df.to_excel(output_excel_path,index=False)

if __name__ == "__main__":
    dataset_name_list = [
        "helpful_base",
        "koala",
        "oasst",
        "self_instruct",
        "vicuna",
    ]
    # for dataset_name in dataset_name_list:
        # get_eval(f"qwen-max...",f"...")