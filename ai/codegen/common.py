import sys

def flatten_name(path, separator="_"):
    return separator.join(path)

def resolve_target_path(current_path, target_str):
    """
    Resolves a target string into a list of path segments.
    Handles:
      - Absolute: "/root/run/c" or "root/run/c"
      - Parent:   "../idle"
      - Sibling:  "b"
      - Deep:     "c/d"
    """
    
    # 1. Absolute Path (Unix style: /run/c)
    if target_str.startswith("/"):
        parts = target_str.strip("/").split("/")
        # Ensure 'root' is the start
        if parts[0] != "root":
            return ["root"] + parts
        return parts

    # 2. Absolute Path (Legacy/Explicit: root/run/c)
    if target_str.startswith("root/"):
        return target_str.split("/")

    # 3. Parent Relative (../idle)
    if target_str.startswith("../"):
        # Go up one level from current state's parent (i.e., go to Uncle)
        # current: [root, run, a]
        # parent:  [root, run]
        # ../:     [root]
        parent_scope = current_path[:-2]
        clean_target = target_str.replace("../", "")
        # Handle "child/grandchild" in target
        return parent_scope + clean_target.split("/")

    # 4. Sibling / Down (b or c/d)
    # Default is to start from the same container (parent)
    parent_scope = current_path[:-1]
    return parent_scope + target_str.split("/")

def get_exit_sequence(source_path, target_path, func_formatter):
    lca_index = 0
    min_len = min(len(source_path), len(target_path))
    
    while lca_index < min_len:
        if source_path[lca_index] != target_path[lca_index]:
            break
        lca_index += 1
    
    # Self-Transition Fix: If source == target, force exit/re-entry
    if lca_index == len(source_path) and lca_index == len(target_path):
        lca_index -= 1

    exits = []
    # Exit from end down to (but not including) the LCA
    for i in range(len(source_path) - 1, lca_index - 1, -1):
        state_segment = source_path[:i+1]
        func_name = func_formatter(state_segment)
        exits.append(func_name)
    return exits

# --- VISUALIZATION ---
# (No changes needed below this line, same as previous version)

def find_composites(name_path, data, result_set):
    my_id = flatten_name(name_path)
    if 'states' in data:
        result_set.add(my_id)
        for child_name, child_data in data['states'].items():
            find_composites(name_path + [child_name], child_data, result_set)

def generate_dot_recursive(name_path, data, lines, composite_ids, decisions):
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
            generate_dot_recursive(name_path + [child_name], child_data, lines, composite_ids, decisions)
        lines.append(f"{indent}}}")
    else:
        lines.append(f"{indent}{my_id} [label=\"{name_path[-1]}\", shape=box, style=\"rounded,filled\", fillcolor=white];")

    # Transitions
    for t in data.get('transitions', []):
        target_str = t['transfer_to']
        is_decision = target_str in decisions
        
        target_path = resolve_target_path(name_path, target_str)
        target_id = flatten_name(target_path)
        
        src = f"{my_id}_start" if is_composite else my_id
        ltail = f"ltail=cluster_{my_id}" if is_composite else ""
        
        if is_decision:
            tgt = target_str
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
    
    for name, transitions in decisions.items():
        lines.append(f"    {name} [label=\"?\", shape=diamond, style=filled, fillcolor=lightyellow];")
        for t in transitions:
            raw_tgt = t['transfer_to']
            # Re-use resolve_target_path for visual accuracy? 
            # For decisions we often just want a rough arrow.
            if raw_tgt.startswith("/"): tgt_id = flatten_name(raw_tgt.strip("/").split("/"))
            elif raw_tgt.startswith("../"): tgt_id = raw_tgt.replace("../", "")
            elif raw_tgt.startswith("root/"): tgt_id = flatten_name(raw_tgt.split("/"))
            else: tgt_id = raw_tgt 
            
            tgt_node = f"{tgt_id}_start" if tgt_id in composite_ids else tgt_id
            lhead = f"lhead=cluster_{tgt_id}" if tgt_id in composite_ids else ""
            
            lbl = str(t.get('test','')).replace('"', '\\"')
            attr = f'label="{lbl}", fontsize=10'
            if lhead: attr += f", {lhead}"
            
            lines.append(f"    {name} -> {tgt_node} [{attr}];")

    lines.append("}")
    return "\n".join(lines)
