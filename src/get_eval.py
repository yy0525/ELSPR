import os
import argparse
import pandas as pd
from utils.eval import get_eval_entropy, get_eval_non_tran, get_DAG_result


def eval_result(flag, dataset_list, dataset_dir, out_dir):
    """
    Evaluate models based on pairwise comparison files and save results to Excel.

    Args:
        flag (str): Evaluation type. 'entropy' or 'non-trans'
        dataset_list (list): List of dataset names to evaluate
        dataset_dir (str): Directory containing dataset files
        out_dir (str): Output directory for saving results
    """
    results = []

    for dataset_name in dataset_list:
        file_path = os.path.join(dataset_dir, dataset_name)

        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            continue

        if flag == "non-trans":
            result = get_eval_non_tran(file_path)
        else:
            result = get_eval_entropy(file_path)

        model_name = os.path.splitext(os.path.basename(file_path))[0]
        result["model_name"] = model_name
        results.append(result)

    df = pd.DataFrame(results)
    output_excel_path = os.path.join(out_dir, f"{flag}_result.xlsx")
    df.to_excel(output_excel_path, index=False)
    print(f"✅ Evaluation results saved to: {output_excel_path}")


def get_without_non_transitivity_result(file_paths, dataset_names, out_dir):
    """
    Process each dataset to remove non-transitive judgments and generate DAGs.

    Args:
        file_paths (list): Paths to the dataset files
        dataset_names (list): Corresponding dataset names
        out_dir (str): Output directory for saving DAG results
    """
    for idx, dataset_name in enumerate(dataset_names):
        file_path = file_paths[idx]
        get_DAG_result(file_path, out_dir, dataset_name)
        print(f"✅ DAG generated for {dataset_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate model comparisons or generate DAG results.")

    parser.add_argument(
        "--mode",
        type=str,
        choices=["eval", "dag"],
        required=True,
        help="Mode to run: 'eval' for evaluation, 'dag' for generating DAG results."
    )

    parser.add_argument(
        "--flag",
        type=str,
        choices=["entropy", "non-trans"],
        default="entropy",
        help="Evaluation method: 'entropy' or 'non-trans'. Only used in 'eval' mode."
    )

    parser.add_argument(
        "--dataset",
        type=str,
        nargs='+',
        default=None,
        help="Specific dataset name(s) to process. Default: all built-in datasets."
    )

    parser.add_argument(
        "--folder-path",
        type=str,
        default="../data/selected_models",
        help="Directory containing dataset files (e.g., helpful_base.json)."
    )

    parser.add_argument(
        "--output-root",
        type=str,
        default="../data/eval_results",
        help="Root directory to store output Excel files and DAG results."
    )

    args = parser.parse_args()

    # Built-in list of supported datasets
    BUILTIN_DATASETS = [
        "helpful_base",
        "koala",
        "oasst",
        "self_instruct",
        "vicuna",
    ]

    dataset_list = args.dataset if args.dataset else BUILTIN_DATASETS
    dataset_dir = args.folder_path
    output_root = args.output_root

    os.makedirs(output_root, exist_ok=True)

    if args.mode == "eval":
        # Run evaluation (either entropy or non-transitivity)
        eval_result(args.flag, dataset_list, dataset_dir, output_root)
    elif args.mode == "dag":
        # Run DAG generation
        file_paths = [os.path.join(dataset_dir, d) for d in dataset_list]
        get_without_non_transitivity_result(file_paths, dataset_list, output_root)

    print("🎉 All tasks completed.")