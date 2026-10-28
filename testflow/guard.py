"""Conservative AST gate: preserve checks, data flow and control flow.

Accepted edits are locator selection changes and added literal Playwright setup
actions. Anything else needs manual review. This is not a Python sandbox or a
proof of business correctness; only trusted generated test files should be run.
"""
import ast
from urllib.parse import urlsplit


class Rejected(ValueError):
    pass


LOCATORS = {'locator', 'get_by_role', 'get_by_text', 'get_by_label', 'get_by_placeholder',
            'get_by_test_id', 'get_by_title', 'get_by_alt_text'}
ACTIONS = {'goto', 'click', 'fill', 'check', 'uncheck', 'select_option', 'hover',
           'press', 'wait_for_selector', 'wait_for_url'}


def is_locator(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr in LOCATORS or (node.func.attr == 'nth' and is_locator(node.func.value))
    return (isinstance(node, ast.Attribute) and node.attr in {'first', 'last'}
            and is_locator(node.value))


class Normalize(ast.NodeTransformer):
    def visit_Attribute(self, node):
        if node.attr in {'first', 'last'} and is_locator(node.value):
            return self.visit(node.value)
        return self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if (node.func.attr == 'nth' and is_locator(node.func.value)
                    and len(node.args) == 1 and not node.keywords
                    and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is int):
                return self.visit(node.func.value)
            if node.func.attr in LOCATORS:
                # Only literal selector arguments can change, never executable expressions.
                for value in [*node.args, *(kw.value for kw in node.keywords)]:
                    if not isinstance(value, ast.Constant):
                        return self.generic_visit(node)
                node.args = [ast.Constant('<selector>')]
                node.keywords = []
        return self.generic_visit(node)


def canonical(node):
    # Parse/unparse a copy: do not mutate the trees being compared.
    copy = ast.parse(ast.unparse(node))
    return ast.dump(Normalize().visit(copy), include_attributes=False)


def _root_name(node):
    while isinstance(node, (ast.Call, ast.Attribute)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


def _extra_action(stmt, pages, origins):
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return False
    call = stmt.value
    if not isinstance(call.func, ast.Attribute) or call.func.attr not in ACTIONS:
        return False
    if _root_name(call) not in pages:
        return False
    # Prevent hidden expressions, file writes, injected functions, or variable replacement.
    for arg in [*call.args, *(kw.value for kw in call.keywords)]:
        if not isinstance(arg, ast.Constant):
            return False
    for node in ast.walk(call.func.value):
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Attribute) or node.func.attr not in LOCATORS:
                return False
            if any(not isinstance(a, ast.Constant) for a in [*node.args, *(k.value for k in node.keywords)]):
                return False
    if call.func.attr == 'goto':
        if not call.args or not isinstance(call.args[0].value, str):
            return False
        if urlsplit(call.args[0].value).netloc not in origins:
            return False
    return True


def validate(original, candidate):
    try:
        old, new = ast.parse(original), ast.parse(candidate)
        compile(new, '<repair>', 'exec')
    except (SyntaxError, ValueError, TypeError) as exc:
        raise Rejected(f'Invalid Python: {exc}') from exc
    if len(candidate) > max(len(original) * 3, 20000):
        raise Rejected('Candidate exceeds size limit')
    origins = {urlsplit(n.value).netloc for n in ast.walk(old)
               if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith(('http://', 'https://'))}
    pages = {'page'}
    for n in ast.walk(old):
        if isinstance(n, ast.FunctionDef):
            pages.update(a.arg for a in n.args.args if a.arg in {'page', 'browser_context'})
    def is_check(node):
        return isinstance(node, ast.Assert) or (isinstance(node, ast.Expr) and any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'expect'
            for n in ast.walk(node)))

    # Preserve the selector inside assertions too: replacing an expected success
    # element with 'body' would otherwise keep to_be_visible() yet weaken the test.
    protected_names = {n.id for stmt in ast.walk(old) if is_check(stmt)
                       for n in ast.walk(stmt) if isinstance(n, ast.Name)} - pages
    assignments = [n for n in ast.walk(old) if isinstance(n, (ast.Assign, ast.AnnAssign))]
    changed = True
    while changed:
        previous = set(protected_names)
        for stmt in assignments:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            bound = {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            if bound & protected_names and stmt.value is not None:
                protected_names.update(n.id for n in ast.walk(stmt.value) if isinstance(n, ast.Name))
        protected_names -= pages
        changed = protected_names != previous

    def protected(stmt):
        if is_check(stmt):
            return True
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            return any(isinstance(n, ast.Name) and n.id in protected_names
                       for target in targets for n in ast.walk(target))
        return False
    def compare(a, b):
        if type(a) is not type(b):
            raise Rejected('Control flow, checks or data assignments changed')
        if isinstance(a, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            for key in a._fields:
                if key == 'body':
                    match_body(a.body, b.body, isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)))
                elif key not in {'type_ignores'}:
                    av, bv = getattr(a, key), getattr(b, key)
                    dump = lambda x: ast.dump(x, include_attributes=False) if isinstance(x, ast.AST) else repr(x)
                    if isinstance(av, list):
                        if [dump(x) for x in av] != [dump(x) for x in bv]:
                            raise Rejected(f'Changed function signature/decorator: {key}')
                    elif dump(av) != dump(bv):
                        raise Rejected(f'Changed declaration: {key}')
        elif protected(a) and ast.dump(a, include_attributes=False) != ast.dump(b, include_attributes=False):
            raise Rejected('Assertions and their data/locator dependencies must remain exact')
        elif canonical(a) != canonical(b):
            raise Rejected('Changed assertion, data flow, control flow, import or unsupported action')

    def match_body(before, after, allow_actions):
        i = j = 0
        while i < len(before):
            a = before[i]
            # A generated script may accidentally import a page fixture from a different test.
            if isinstance(a, ast.ImportFrom) and (a.module or '').startswith('generated_tests.'):
                if j >= len(after) or canonical(a) != canonical(after[j]):
                    if all(alias.name == 'page' and alias.asname is None for alias in a.names):
                        i += 1
                        continue
            if j >= len(after):
                raise Rejected('Removed existing test statements')
            b = after[j]
            if type(a) is type(b) and (isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)) or canonical(a) == canonical(b)):
                compare(a, b)
                i += 1
                j += 1
            elif allow_actions and _extra_action(b, pages, origins):
                j += 1
            else:
                raise Rejected('Existing checks/actions/data must remain; only locator edits and added setup actions are automatic')
        if any(not allow_actions or not _extra_action(x, pages, origins) for x in after[j:]):
            raise Rejected('Unsupported added code')
    compare(old, new)
    return True
