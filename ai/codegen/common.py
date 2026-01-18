import sys
import re

def flatten_name(path, separator="_"):
    return separator.join(path)

# --- NEW: Helper for Graphviz IDs ---
def get_graph_id(path):
    """
    Creates a unique, safe ID for Graphviz.
    1. Joins with double underscore '__' to prevent collisions with user underscores.
    2. Replaces non-alphanumeric characters (like '-') with '_'.
    """
    # Join with distinct separator
    raw_id = "__".join(path)
    # Replace anything that isn't a-z, A-Z, 0-9, or _
    safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', raw_id)
    return safe_id

def resolve_target_path(current_path, target_str):
    if target_str.startswith("/"):
        parts = target_str.strip("/").split("/")
        if parts[0] != "root": return ["root"] + parts
        return parts
    if target_str.startswith("root/"): return target_str.split("/")
    if target_str.startswith("../"):
        parent_scope = current_path[:-2]
        clean_target = target_str.replace("../", "")
        return parent_scope + clean_target.split("/")
    
    parent_scope = current_path[:-1]
    return parent_scope + target_str.split("/")

def get_lca_index(source_path, target_path):
    lca_index = 0
    min_len = min(len(source_path), len(target_path))
    while lca_index < min_len:
        if source_path[lca_index] != target_path[lca_index]:
            break
        lca_index += 1
    if lca_index == len(source_path) and lca_index == len(target_path):
        lca_index -= 1
    return lca_index

def get_exit_sequence(source_path, target_path, func_formatter):
    lca_index = get_lca_index(source_path, target_path)
    exits = []
    for i in range(len(source_path) - 1, lca_index - 1, -1):
        state_segment = source_path[:i+1]
        func_name = func_formatter(state_segment)
        exits.append(func_name)
    return exits

def get_entry_sequence(source_path, target_path, func_formatter):
    lca_index = get_lca_index(source_path, target_path)
    if lca_index == len(target_path):
        lca_index -= 1

    entries = []
    for i in range(lca_index, len(target_path)):
        state_segment = target_path[:i+1]
        suffix = "_entry" if i == len(target_path) - 1 else "_start"
        func_name = func_formatter(state_segment, suffix)
        entries.append(func_name)
    return entries

# --- VISUALIZATION ---

def find_composites(name_path, data, result_set):
    # Use SAFE ID for set storage
    my_id = get_graph_id(name_path)
    if 'states' in data:
        result_set.add(my_id)
        for child_name, child_data in data['states'].items():
            find_composites(name_path + [child_name], child_data, result_set)

def generate_dot_recursive(name_path, data, lines, composite_ids, decisions):
    # Use SAFE ID for node definition
    my_id = get_graph_id(name_path)
    
    is_composite = 'states' in data
    indent = "    " * len(name_path)

    if is_composite:
        # Cluster names MUST start with 'cluster_' to be drawn as boxes
        lines.append(f"{indent}subgraph cluster_{my_id} {{")
        lines.append(f"{indent}    label = \"{name_path[-1]}\";")
        
        if data.get('parallel', False):
             lines.append(f"{indent}    style=dashed; color=black; penwidth=1.5; node [style=filled, fillcolor=white];")
             # Anchors for compound edges
             lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
             
             for child_name, child_data in data['states'].items():
                 child_path = name_path + [child_name]
                 child_id = get_graph_id(child_path)
                 
                 tgt = f"{child_id}_start" if child_id in composite_ids else child_id
                 lhead = f"lhead=cluster_{child_id}" if child_id in composite_ids else ""
                 
                 lines.append(f"{indent}    {my_id}_start -> {tgt} [style=dashed, {lhead}];")
        else:
             lines.append(f"{indent}    style=rounded; color=black; penwidth=1.0; node [style=filled, fillcolor=white];")
             if data.get('history', False):
                 lines.append(f"{indent}    {my_id}_hist [shape=circle, label=\"H\", width=0.3];")
             
             init_child_path = name_path + [data['initial']]
             init_child_id = get_graph_id(init_child_path)
             
             tgt = f"{init_child_id}_start" if init_child_id in composite_ids else init_child_id
             lhead = f"lhead=cluster_{init_child_id}" if init_child_id in composite_ids else ""
             
             lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
             lines.append(f"{indent}    {my_id}_start -> {tgt} [{lhead}];")

        for child_name, child_data in data['states'].items():
            generate_dot_recursive(name_path + [child_name], child_data, lines, composite_ids, decisions)
        lines.append(f"{indent}}}")
    else:
        # Leaf Node
        label = name_path[-1]
        shape = "box"
        style = "rounded,filled"
        
        # Decision visualization override (if users use transient states as decisions)
        if data.get('decision', False):
            shape = "diamond"
            style = "filled"
            label = "" 
        
        lines.append(f"{indent}{my_id} [label=\"{label}\", shape={shape}, style=\"{style}\", fillcolor=white];")

    # Transitions
    for t in data.get('transitions', []):
        target_str = t['transfer_to']
        is_decision = target_str in decisions
        
        target_path = resolve_target_path(name_path, target_str)
        target_id = get_graph_id(target_path)
        
        # Source is usually 'my_id' (or my_id_start if composite)
        # But visually, transitions usually originate from the box itself
        src = f"{my_id}_start" if is_composite else my_id
        ltail = f"ltail=cluster_{my_id}" if is_composite else ""
        
        if is_decision:
            # Decisions are at root usually, need safe ID
            tgt = get_graph_id(['root', target_str]) if target_str in decisions else target_str
            lhead = ""
        else:
            tgt = f"{target_id}_start" if target_id in composite_ids else target_id
            lhead = f"lhead=cluster_{target_id}" if target_id in composite_ids else ""

        attrs = [x for x in [ltail, lhead] if x]
        raw_test = t.get('test', '')
        safe_label = str(raw_test).replace('"', '\\"')
        attrs.append(f'label="{safe_label}"')
        attrs.append('fontsize=10')
        
        lines.append(f"{indent}{src} -> {tgt} [{', '.join(attrs)}];")

def generate_dot(root_data, decisions):
    composite_ids = set()
    find_composites(['root'], root_data, composite_ids)
    
    lines = ["digraph StateMachine {", "    compound=true; fontname=\"Arial\"; node [fontname=\"Arial\"]; edge [fontname=\"Arial\"];"]
    
    generate_dot_recursive(['root'], root_data, lines, composite_ids, decisions)
    
    # Decisions (Diamonds)
    for name, transitions in decisions.items():
        # Safe ID for decision node
        dec_id = get_graph_id(['root', name])
        lines.append(f"    {dec_id} [label=\"?\", shape=diamond, style=filled, fillcolor=lightyellow];")
        
        for t in transitions:
            raw_tgt = t['transfer_to']
            target_path = resolve_target_path(['root', name], raw_tgt) # Treat decision as if at root
            target_id = get_graph_id(target_path)
            
            tgt_node = f"{target_id}_start" if target_id in composite_ids else target_id
            lhead = f"lhead=cluster_{target_id}" if target_id in composite_ids else ""
            
            lbl = str(t.get('test','')).replace('"', '\\"')
            attr = f'label="{lbl}", fontsize=10'
            if lhead: attr += f", {lhead}"
            
            lines.append(f"    {dec_id} -> {tgt_node} [{attr}];")

    lines.append("}")
    return "\n".join(lines)
