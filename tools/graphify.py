"""
graphify - build a knowledge graph of the LittleCat codebase.

Parses src/*.py with `ast` and emits:
  docs/graph/project_graph.json   nodes (module/class/function/data) + edges
  docs/graph/PROJECT_GRAPH.md     Mermaid diagrams (modules, brain flow)

Usage:  python tools/graphify.py
"""

import ast
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "docs", "graph")


def analyse():
    nodes, edges = {}, set()
    method_owner = {}  # method name -> [qualified ids]
    trees = {}
    for fname in sorted(os.listdir(SRC)):
        if not fname.endswith(".py"):
            continue
        mod = fname[:-3]
        path = os.path.join(SRC, fname)
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source)
        trees[mod] = tree
        nodes[f"module:{mod}"] = {"id": f"module:{mod}", "type": "module", "label": mod,
                                  "loc": source.count("\n") + 1, "file": f"src/{fname}"}
        for item in tree.body:
            if isinstance(item, ast.ClassDef):
                cid = f"class:{mod}.{item.name}"
                nodes[cid] = {"id": cid, "type": "class", "label": item.name, "file": f"src/{fname}",
                              "line": item.lineno, "loc": item.end_lineno - item.lineno + 1}
                edges.add((f"module:{mod}", "defines", cid))
                for fn in item.body:
                    if isinstance(fn, ast.FunctionDef):
                        fid = f"func:{mod}.{item.name}.{fn.name}"
                        nodes[fid] = {"id": fid, "type": "method", "label": fn.name, "file": f"src/{fname}",
                                      "line": fn.lineno, "loc": fn.end_lineno - fn.lineno + 1}
                        edges.add((cid, "has_method", fid))
                        method_owner.setdefault(fn.name, []).append(fid)
            elif isinstance(item, ast.FunctionDef):
                fid = f"func:{mod}.{item.name}"
                nodes[fid] = {"id": fid, "type": "function", "label": item.name, "file": f"src/{fname}",
                              "line": item.lineno, "loc": item.end_lineno - item.lineno + 1}
                edges.add((f"module:{mod}", "defines", fid))
                method_owner.setdefault(item.name, []).append(fid)

    local_modules = set(trees)
    for mod, tree in trees.items():
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                target = n.module.lstrip(".").split(".")[0]
                if target in local_modules:
                    edges.add((f"module:{mod}", "imports", f"module:{target}"))
            elif isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name in local_modules:
                        edges.add((f"module:{mod}", "imports", f"module:{alias.name}"))
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith(".json"):
                did = f"data:{os.path.basename(n.value)}"
                nodes.setdefault(did, {"id": did, "type": "data", "label": os.path.basename(n.value)})
                edges.add((f"module:{mod}", "reads_writes", did))

        # call edges between functions (name-based resolution, cross-module aware)
        for scope in ast.walk(tree):
            if not isinstance(scope, ast.FunctionDef):
                continue
            caller = _qualify(nodes, mod, scope)
            if not caller:
                continue
            for call in ast.walk(scope):
                if isinstance(call, ast.Call):
                    name = call.func.attr if isinstance(call.func, ast.Attribute) else \
                        call.func.id if isinstance(call.func, ast.Name) else None
                    allowed = {mod} | {b.split(":")[1] for a, r, b in edges
                                       if a == f"module:{mod}" and r == "imports"}
                    for target in method_owner.get(name, []):
                        target_mod = target.split(":")[1].split(".")[0]
                        if target != caller and target_mod in allowed and _plausible(mod, target, call.func):
                            edges.add((caller, "calls", target))

    data_files = ("cats/<name>.json", "profiles.json", "exports/profile_*.json")
    for d in data_files:
        did = f"data:{d}"
        nodes[did] = {"id": did, "type": "data", "label": d}
    edges.add(("func:cat_brain.CatBrain.save_brain", "writes", "data:cats/<name>.json"))
    edges.add(("func:cat_brain.CatBrain.load_brain", "reads", "data:cats/<name>.json"))
    edges.add(("func:game.LittleCatGame.save_profiles_index", "writes", "data:profiles.json"))
    edges.add(("func:game.LittleCatGame.export_profile", "writes", "data:exports/profile_*.json"))

    edge_list = [{"from": a, "rel": r, "to": b} for a, r, b in sorted(edges) if a in nodes and b in nodes]
    return {"schema": "littlecat.codegraph/v1", "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
            "edges": edge_list}


def _qualify(nodes, mod, fn):
    for nid in (f"func:{mod}.{fn.name}",):
        if nid in nodes:
            return nid
    for nid, node in nodes.items():
        if nid.startswith(f"func:{mod}.") and nid.endswith(f".{fn.name}") and node.get("line") == fn.lineno:
            return nid
    return None


def _plausible(mod, target, func):
    # self.foo() only resolves inside the same module; obj.foo()/foo() may cross modules
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self":
        return target.startswith(f"func:{mod}.")
    return True


def mermaid(graph):
    mods = [n for n in graph["nodes"] if n["type"] == "module"]
    lines = ["```mermaid", "graph LR"]
    for m in mods:
        lines.append(f'  {m["label"]}["{m["label"]}.py<br/>{m["loc"]} LOC"]')
    seen = set()
    for e in graph["edges"]:
        if e["rel"] == "imports":
            a, b = e["from"].split(":")[1], e["to"].split(":")[1]
            lines.append(f"  {a} -->|imports| {b}")
        elif e["rel"] == "calls":
            a = e["from"].split(":")[1].split(".")[0]
            b = e["to"].split(":")[1].split(".")[0]
            if a != b and (a, b) not in seen:
                seen.add((a, b))
                lines.append(f"  {a} -.->|calls| {b}")
    lines.append("```")
    return "\n".join(lines)


def brain_flow(graph):
    wanted = re.compile(r"func:(cat_brain|memory_graph|autonomy|game\.LittleCatGame\.(update|perform_action|auto_perform_action|play_with_toy|resolve_mini_game|run|save_all_profiles))")
    keep = {n["id"] for n in graph["nodes"] if wanted.match(n["id"])}
    lines = ["```mermaid", "graph TD"]
    ids = {}
    for e in graph["edges"]:
        if e["rel"] == "calls" and e["from"] in keep and e["to"] in keep:
            for nid in (e["from"], e["to"]):
                ids.setdefault(nid, f"n{len(ids)}")
            short = lambda x: ".".join(x.split(":")[1].split(".")[-2:])
            lines.append(f'  {ids[e["from"]]}["{short(e["from"])}"] --> {ids[e["to"]]}["{short(e["to"])}"]')
    lines.append("```")
    return "\n".join(lines)


def main():
    graph = analyse()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "project_graph.json"), "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2)
    counts = {}
    for n in graph["nodes"]:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    biggest = sorted((n for n in graph["nodes"] if n["type"] in ("method", "function")),
                     key=lambda n: n["loc"], reverse=True)[:8]
    md = ["# LittleCat - project graph", "",
          "Generated by `python tools/graphify.py` (do not edit by hand).", "",
          f"Nodes: {counts} - edges: {len(graph['edges'])}", "",
          "## Modules", "", mermaid(graph), "",
          "## Brain / learning flow (calls)", "", brain_flow(graph), "",
          "## Largest functions (refactor candidates)", "",
          "| function | file | LOC |", "|---|---|---|"]
    md += [f"| `{n['id'][5:]}` | {n['file']}:{n['line']} | {n['loc']} |" for n in biggest]
    with open(os.path.join(OUT, "PROJECT_GRAPH.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"graph: {counts}, {len(graph['edges'])} edges -> {OUT}")


if __name__ == "__main__":
    main()
