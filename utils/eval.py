from tournament_graph import *
def load_jsonl(file_path):
    """Load jsonl file."""
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try :
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error in line {line_number}: {e}")
                continue
def bulid_graphs_from_jsonl(file_path):
    graphs = {}
    for item in load_jsonl(file_path):
        question_id = item["question_id"]
        model_1 = item["model_1"]
        model_2 = item["model_2"]
        g1_winner = item["g1_winner"]
        g2_winner = item["g2_winner"]

        if question_id not in graphs:
            graphs[question_id] = TournamentGraph()
        graphs = graphs[question_id]
        winner = g1_winner
        if winner == "modle_1":
            graphs.add_edge(model_1, model_2, "win")
        elif winner == "modle_2":
            graphs.add_edge(model_1, model_2, "lose")
        elif winner == "tie":
            graphs.add_edge(model_1, model_2, "tie")
        winner = g2_winner
        if winner == "modle_1":
            graphs.add_edge(model_1, model_2, "win")
        elif winner == "modle_2":
            graphs.add_edge(model_1, model_2, "lose")
        elif winner == "tie":
            graphs.add_edge(model_1, model_2, "tie")
    return graphs

def analyze_graphs_info(graphs):
    analyze_results = {}
    for question_id, graph in graphs.items():
        sccs = graph.find_scc()
        filtered_scc= [scc for scc in sccs if not graph.is_all_tie_scc(scc)]
        analyze_results[question_id] = {
            "filtered_scc": filtered_scc
        }
    return analyze_results

def count_infos_filtered_sccs(analyze_results):
    scc_count_infos = {}
    for question_id, result in analyze_results.items():
        filtered_scc = result['filtered_scc']
        num_cycles = len(filtered_scc)
        models_in_scc = set()
        for scc in filtered_scc:
            models_in_scc.update(scc)
        num_unique_models = len(models_in_scc)
        sum_cycles_length = 0
        for c in filtered_scc:
            sum_cycles_length += len(c)
        scc_count_infos[question_id] = {
            'num_scc': num_cycles,
            'num_unique_models': num_unique_models,
            'models_in_scc': list(models_in_scc),
            'scc': result['filtered_scc']
        }
    return scc_count_infos


def get_eval_non_tran(file_path):
    graphs = bulid_graphs_from_jsonl(file_path)
    analyze_results = analyze_graphs_info(graphs)
    sorted_question_ids = sorted(analyze_results.keys())
    scc_count_infos = count_infos_filtered_sccs(analyze_results)

    total_scc_num = 0
    total_scc_model_num = 0
    for question_id in sorted_question_ids:
        total_scc_num += scc_count_infos[question_id]["num_scc"]
        total_scc_model_num += scc_count_infos[question_id]["num_unique_models"]
    return {
        "question number": len(sorted_question_ids),
        "scc num": total_scc_num,
        "scc model num": total_scc_model_num,
        "non-transitivity": f"{total_scc_model_num/(7*len(sorted_question_ids))*100:0.2f}%"
    }
def get_eval_entropy(file_path):
    graphs = bulid_graphs_from_jsonl(file_path)
    two_d_entrop_results = {}
    for question_id, graph in graphs.items():
        two_d_entrop = graph.calculate_2d_entropies()
        two_d_entrop_results[question_id] = two_d_entrop
    total_two_d_entropy = 0
    total_normalized_two_d_entropy = 0
    sorted_question_ids = sorted(two_d_entrop_results.keys())
    for question_id in sorted_question_ids:
        total_two_d_entropy += two_d_entrop_results[question_id]["structutal_entropy"]
        total_normalized_two_d_entropy += two_d_entrop_results[question_id]["normalized_entropy"]
    return {
        "question number": len(sorted_question_ids),
        "Ave structutal_entropy": total_two_d_entropy/len(sorted_question_ids),
        "Ave normalized_entropy": total_normalized_two_d_entropy/len(sorted_question_ids),
    }

def get_DAG_result(file_path,out_dir,model_name):
    graphs = bulid_graphs_from_jsonl(file_path)
    for question_id, graph in graphs.items():
        sccs = graph.find_scc()
        graph.resolve_cycles(sccs)
        graph.export_judgments(question_id,out_dir+f"{model_name}_DAG_result.jsonl")
