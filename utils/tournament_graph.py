import math
import json
from collections import defaultdict
from itertools import combinations


class TournamentGraph:
    def __init__(self):
        """
        Initialize the tournament graph.

        - graph: adjacency list representing model comparison relationships.
        - conflicts: set of conflicting node pairs (inconsistent comparisons).
        - tie_set: set of tied node pairs.
        """
        self.graph = defaultdict(list)  # Adjacency list representation of the graph
        self.conflicts = set()  # Store conflicting comparisons (e.g., A > B and B > A)
        self.tie_set = set()  # Store tied comparisons

    def add_edge(self, node1, node2, relation):
        """
        Add an edge between two models based on their comparison result.

        Args:
            node1: First model name
            node2: Second model name
            relation: "win", "lose", or "tie"

        Returns:
            True if edge was added successfully
        """
        # Handle tie relationship
        if relation == "tie":
            if ((node1 in self.graph[node2] and node2 not in self.graph[node1]) or
                    (node2 in self.graph[node1] and node1 not in self.graph[node2])):
                self.conflicts.add((node1, node2))
        elif relation == "win":
            if node1 in self.graph[node2]:  # Conflicting edge
                self.conflicts.add((node1, node2))
        elif relation == "lose":
            if node2 in self.graph[node1]:  # Conflicting edge
                self.conflicts.add((node1, node2))

        # Add actual edge
        if relation == "win":
            if node2 not in self.graph[node1]:
                self.graph[node1].append(node2)
        elif relation == "lose":
            if node1 not in self.graph[node2]:
                self.graph[node2].append(node1)
        elif relation == "tie":
            self.tie_set.add((node1, node2))
            self.tie_set.add((node2, node1))
            if node2 not in self.graph[node1]:
                self.graph[node1].append(node2)
            if node1 not in self.graph[node2]:
                self.graph[node2].append(node1)

        return True

    def normalize_cycle(self, cycle):
        """
        Normalize a cycle by rotating it to start with the smallest node.

        Args:
            cycle: List of nodes forming a cycle

        Returns:
            Normalized cycle as a tuple
        """
        if not cycle:
            return []

        min_node = min(cycle)
        indices = [i for i, node in enumerate(cycle) if node == min_node]
        candidates = []
        for idx in indices:
            candidate = cycle[idx:] + cycle[:idx]
            candidates.append(tuple(candidate))
        return min(candidates) if candidates else []

    def find_scc(self):
        """
        Find all strongly connected components (SCCs) using Tarjan's algorithm.

        Returns:
            List of cycles (SCCs) found in the graph
        """
        index_counter = [0]
        stack = []
        low = {}
        index = {}
        on_stack = set()
        cycles = []

        def tarjan(node):
            index[node] = index_counter[0]
            low[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack.add(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in index:
                    tarjan(neighbor)
                    low[node] = min(low[node], low[neighbor])
                elif neighbor in on_stack:
                    low[node] = min(low[node], index[neighbor])

            if low[node] == index[node]:
                cycle = []
                while True:
                    current = stack.pop()
                    on_stack.remove(current)
                    cycle.append(current)
                    if current == node:
                        break
                normalized_cycle = self.normalize_cycle(cycle)
                if normalized_cycle:
                    cycles.append(normalized_cycle)

        for node in self.graph:
            if node not in index:
                tarjan(node)

        return cycles

    def is_all_tie_scc(self, scc):
        """
        Check whether all nodes in an SCC are mutually tied.

        Args:
            scc: List of nodes in an SCC

        Returns:
            True if all pairwise ties exist within the SCC
        """
        for i in range(len(scc)):
            for j in range(i + 1, len(scc)):
                if (scc[i], scc[j]) not in self.tie_set:
                    return False
        return True

    def resolve_cycles(self, filtered_cycles):
        """
        Resolve cyclic dependencies among models.

        Args:
            filtered_cycles: List of cycles to be resolved
        """
        nodes_to_process = set()
        for cycle in filtered_cycles:
            nodes_to_process.update(cycle)

        if not nodes_to_process:
            return

        degree_groups = {}
        for node in nodes_to_process:
            in_degree = sum(1 for k, v in self.graph.items() if node in v)
            if in_degree not in degree_groups:
                degree_groups[in_degree] = set()
            degree_groups[in_degree].add(node)

        sorted_degree = sorted(degree_groups.keys(), reverse=True)

        # Build edges between nodes based on group relations
        for i in range(len(sorted_degree) - 1):
            current_degree = sorted_degree[i]
            lower_degrees = sorted_degree[i + 1:]
            for lower_degree in lower_degrees:
                higher_nodes = degree_groups[current_degree]
                lower_nodes = degree_groups[lower_degree]
                for u in higher_nodes:
                    for v in lower_nodes:
                        if v not in self.graph.get(u, []):
                            self.graph[u].append(v)

        # Update edges according to hierarchy
        for i in range(len(sorted_degree)):
            current_degree = sorted_degree[i]
            for u in degree_groups[current_degree]:
                new_edges = []
                for v in self.graph.get(u, []):
                    if v in degree_groups.get(current_degree, set()):
                        new_edges.append(v)
                self.graph[u] = new_edges

    def export_judgments(self, question_id, output_path):
        """
        Export judgments into JSONL format.

        Args:
            question_id: ID of the question being judged
            output_path: Path to write output file
        """
        nodes = sorted(self.graph.keys())
        records = {}

        for u, v in combinations(nodes, 2):
            u, v = sorted([u, v])
            key = f"{u}||{v}"

            has_u_to_v = v in self.graph.get(u, [])
            has_v_to_u = u in self.graph.get(v, [])

            if has_u_to_v and has_v_to_u:
                winner = "tie"
            elif has_u_to_v:
                winner = "model_1"
            elif has_v_to_u:
                winner = "model_2"
            else:
                continue

            records[key] = {
                "question_id": str(question_id),
                "winner": winner,
                "model_1": u,
                "model_2": v,
            }

        with open(output_path, "a") as f:
            for record in records.values():
                f.write(json.dumps(record) + "\n")

    def calculate_2d_entropies(self):
        """
        Calculate structural entropy and normalized entropy of the tournament graph.

        Returns:
            Dictionary containing:
            - structutal_entropy: Structural uncertainty in the graph
            - normalized_entropy: Entropy normalized by number of nodes
        """
        sccs = self.find_scc()
        node_to_scc = {}
        for idx, scc in enumerate(sccs):
            for node in scc:
                node_to_scc[node] = idx

        num_partition = len(sccs)
        scc_size = [len(scc) for scc in sccs]

        d_in = defaultdict(int)
        vol = defaultdict(int)
        g = defaultdict(int)
        total_edges = 0

        for u in self.graph:
            for v in self.graph[u]:
                total_edges += 1
                src_scc = node_to_scc.get(v, -1)
                tgt_scc = node_to_scc.get(u, -1)

                if src_scc == -1 or tgt_scc == -1:
                    continue

                d_in[u] += 1
                vol[tgt_scc] += 1

                if src_scc != tgt_scc:
                    size_src = scc_size[src_scc]
                    size_tgt = scc_size[tgt_scc]
                    if size_src > 1 or size_tgt > 1:
                        g[tgt_scc] += 1

        m = total_edges
        if m == 0:
            return {"structutal_entropy": 0.0, "normalized_entropy": 0.0}

        H_part1 = 0.0
        for j in range(num_partition):
            vol_j = vol.get(j, 0)
            if vol_j == 0:
                continue
            partition_nodes = sccs[j]
            entropy = 0.0
            for node in partition_nodes:
                din = d_in.get(node, 0)
                if din == 0:
                    continue
                p = din / vol_j
                entropy += p * math.log(p)
            H_part1 += (vol_j / m) * entropy
        H_part1 *= -1

        H_part2 = 0.0
        for j in range(num_partition):
            g_j = g.get(j, 0)
            vol_j = vol.get(j, 0)
            if vol_j == 0 or m == 0:
                continue
            ratio = vol_j / m
            term = (g_j / m) * math.log2(ratio)
            H_part2 += term
        H_part2 *= -1

        structutal_entropy = H_part1 + H_part2
        normalized_entropy = structutal_entropy / math.log2(sum(scc_size)) if sum(scc_size) > 0 else 0.0

        return {
            "structutal_entropy": structutal_entropy,
            "normalized_entropy": normalized_entropy,
        }