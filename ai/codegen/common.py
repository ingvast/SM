import sys

# --- HELPER FUNCTIONS ---

def flatten_name(path, separator="_"):
    return separator.join(path)

def resolve_target_path(current_path, target_str):
    if target_str.startswith("root/"):
        return target_str.split("/")
    if target_str.startswith("../"):
        # Go up: ../ means parent of current scope
        parent_scope = current_path[:-2]
        clean_target = target_str.replace("../", "")
        return parent_scope + [clean_target]
    # Sibling
    parent_scope = current_path[:-1]
    return parent_scope + [target_str]

def get_exit_sequence(source_path, target_path, func_formatter):
    """
    Calculates the sequence of states to exit.
    func_formatter: function that takes a path list and returns the function name.
    """
    lca_index = 0
    min_len = min(len(source_path), len(target_path))
    while lca_index < min_len:
        if source_path[lca_index] != target_path[lca_index]:
            break
        lca_index += 1
    
    exits = []
    # Exit from end down to LCA
    for i in range(len(source_path) - 1, lca_index - 1, -1):
        state_segment = source_path[:i+1]
        func_name = func_formatter(state_segment)
        exits.append(func_name)
    return exits

# --- DOT GENERATOR (Language Agnostic) ---

def find_composites(name_path, data, result_set):
    my_id = flatten_name(name_path)
    if 'states' in data:
        result_set.add(my_id)
        for child_name, child_data in data['states'].items():
            find_composites(name_path + [child_name], child_data, result_set)

def generate_dot_recursive(name_path, data, lines, composite_ids):
    my_id = flatten_name(name_path)
    is_composite = 'states' in data
    indent = "    " * len(name_path)

    if is_composite:
        lines.append(f"{indent}subgraph cluster_{my_id} {{")
        lines.append(f"{indent}    label = \"{name_path[-1]}\";")
        if data.get('parallel', False):
             lines.append(f"{indent}    style=dashed; color=black; penwidth=1.5; node [style=filled, fillcolor=white];")
             lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
             for child_name, child_data in data['states'].items():
                 child_id = flatten_name(name_path + [child_name])
                 tgt = f"{child_id}_start" if child_id in composite_ids else child_id
                 lhead = f"lhead=cluster_{child_id}" if child_id in composite_ids else ""
                 lines.append(f"{indent}    {my_id}_start -> {tgt} [style=dashed, {lhead}];")
        else:
             lines.append(f"{indent}    style=rounded; color=black; penwidth=1.0; node [style=filled, fillcolor=white];")
             if data.get('history', False):
                 lines.append(f"{indent}    {my_id}_hist [shape=circle, label=\"H\", width=0.3];")
             
             init_child_id = flatten_name(name_path + [data['initial']])
             tgt = f"{init_child_id}_start" if init_child_id in composite_ids else init_child_id
             lhead = f"lhead=cluster_{init_child_id}" if init_child_id in composite_ids else ""
             lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
             lines.append(f"{indent}    {my_id}_start -> {tgt} [{lhead}];")

        for child_name, child_data in data['states'].items():
            generate_dot_recursive(name_path + [child_name], child_data, lines, composite_ids)
        lines.append(f"{indent}}}")
    else:
        lines.append(f"{indent}{my_id} [label=\"{name_path[-1]}\", shape=box, style=\"rounded,filled\", fillcolor=white];")

    for t in data.get('transitions', []):
        target_path = resolve_target_path(name_path, t['transfer_to'])
        target_id = flatten_name(target_path)
        src = f"{my_id}_start" if is_composite else my_id
        ltail = f"ltail=cluster_{my_id}" if is_composite else ""
        tgt = f"{target_id}_start" if target_id in composite_ids else target_id
        lhead = f"lhead=cluster_{target_id}" if target_id in composite_ids else ""
        
        attrs = [x for x in [ltail, lhead] if x]
        raw_test = t.get('test', '')
        # Escape quotes
        safe_label = str(raw_test).replace('"', '\\"')
        attrs.append(f'label="{safe_label}"')
        attrs.append('fontsize=10')
        lines.append(f"{indent}{src} -> {tgt} [{', '.join(attrs)}];")

def generate_dot(root_data):
    composite_ids = set()
    find_composites(['root'], root_data, composite_ids)
    lines = ["digraph StateMachine {", "    compound=true; fontname=\"Arial\"; node [fontname=\"Arial\"]; edge [fontname=\"Arial\"];"]
    generate_dot_recursive(['root'], root_data, lines, composite_ids)
    lines.append("}")
    return "\n".join(lines)
