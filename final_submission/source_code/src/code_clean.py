import ast
import io
import re
import tokenize

DASHES = {"—": "-", "–": "-", "−": "-"}


def _docstring_ranges(tree):
    ranges = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                first = body[0]
                ranges.append((first.lineno, first.end_lineno, first.col_offset, len(body) == 1))
    return ranges


def strip_python(source):
    tree = ast.parse(source)
    lines = source.split("\n")
    drop = set()
    replace = {}
    for start, end, col, only in _docstring_ranges(tree):
        for n in range(start, end + 1):
            drop.add(n)
        if only:
            replace[start] = " " * col + "pass"
            drop.discard(start)
    comment_cols = {}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            comment_cols[tok.start[0]] = tok.start[1]
    out = []
    for i, line in enumerate(lines, 1):
        if i in drop:
            continue
        if i in replace:
            out.append(replace[i])
            continue
        if i in comment_cols:
            line = line[:comment_cols[i]].rstrip()
            if not line.strip():
                continue
        out.append(line.rstrip())
    text = "\n".join(out)
    for k, v in DASHES.items():
        text = text.replace(k, v)
    text = re.sub(r" {2,}# [^\n\"]*", "", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = text.strip("\n") + "\n"
    ast.parse(text)
    return text


def strip_requirements(source):
    out = []
    for line in source.split("\n"):
        line = line.split("#", 1)[0].rstrip()
        if line.strip():
            out.append(line)
    return "\n".join(out) + "\n"


def leftover_comment_like(text):
    return [l for l in text.split("\n") if l.lstrip().startswith("#")]
