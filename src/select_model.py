import os
import json
from collections import defaultdict
import argparse
def load_model_data(model_dir):
    """Load all .json files from the model directory."""
    all_data = defaultdict(list)

    for file_name in os.listdir(model_dir):
        if not file_name.endswith(".json"):
            continue

        file_path = os.path.join(model_dir, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        dataset = item.get("dataset")
                        if dataset:
                            all_data[dataset].append(item)
                else:
                    dataset = data.get("dataset")
                    if dataset:
                        all_data[dataset].append(data)

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return all_data


def filter_by_dataset(data_dict, target_datasets):
    """Filter data by specified dataset names."""
    filtered = defaultdict(list)
    target_datasets = set(d.lower() for d in target_datasets)

    for dataset, items in data_dict.items():
        if dataset.lower() in target_datasets:
            filtered[dataset] = items

    return filtered


def save_to_files(dataset_dict, output_root, model_name):
    """Save each dataset into a separate JSON file."""
    for dataset, items in dataset_dict.items():
        output_dir = os.path.join(output_root, model_name)
        output_file = os.path.join(output_dir, f"{dataset}.json")

        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"[{model_name}] Saved {len(items)} records to {dataset}.json")


def process_model(model_name, args):
    """Process data under a single model directory."""
    model_dir = os.path.join(args.folder_path, model_name)
    if not os.path.isdir(model_dir):
        return

    print(f"Processing model: {model_name}")

    # Load data
    raw_data = load_model_data(model_dir)

    # Determine datasets to process
    if args.dataset:
        datasets = args.dataset
    else:
        datasets = ["helpful_base", "koala", "oasst", "selfinstruct", "vicuna"]

    # Filter by specified datasets
    filtered_data = filter_by_dataset(raw_data, datasets)

    # Save results
    save_to_files(filtered_data, args.output_root, model_name)


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
        "--folder-path",
        type=str,
        default="../model_results",
        help="Path to the root folder containing model directories. Default: ../model_results"
    )

    parser.add_argument(
        "--output-root",
        type=str,
        default="../data/selected_models",
        help="Root path for output files. Default: ../data/selected_models"
    )
    args = parser.parse_args()

    # Get list of models to process
    if args.model_name:
        model_names = args.model_name
    else:
        model_names = os.listdir(args.folder_path)

    for model_name in model_names:
        process_model(model_name, args)
        print(model_name)



