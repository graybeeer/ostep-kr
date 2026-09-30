"""Run with Python 3.9+: python tests/check_korean.py (standard library only).

Compare against the pinned upstream Git commit, never the moving HEAD.
Only presentation literals and the explicit reading-guide print may differ.
"""
import ast
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
UPSTREAM = 'afb36ca8ddbf81d847d18f6bd18a87f0a18667f2'
GUIDE = '\n[각주: 출력 읽는 법]\n'
FORMAT = re.compile(r'%(?:\([^)]+\))?[#0 +\-]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?[diouxXeEfFgGcrsa%]')


def literals(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node
    elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        yield from literals(node.left)
        yield from literals(node.right)
    elif isinstance(node, ast.Tuple):
        for item in node.elts:
            yield from literals(item)
    elif isinstance(node, ast.IfExp):
        yield from literals(node.body)
        yield from literals(node.orelse)


def normalized(source):
    tree = ast.parse(source)
    guides = []
    for node in list(tree.body):
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print'
                and len(node.value.args) == 1 and isinstance(node.value.args[0], ast.Constant)
                and isinstance(node.value.args[0].value, str) and node.value.args[0].value.startswith(GUIDE)):
            guides.append(node)
            tree.body.remove(node)
    assert len(guides) <= 1, 'A reading guide must appear only once'
    seen = set()
    formats = []
    formatted = {id(literal) for node in ast.walk(tree)
                 if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)
                 for literal in literals(node.left)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        candidates = []
        if isinstance(node.func, ast.Name):
            if node.func.id == 'print':
                candidates.extend(node.args)
            elif node.func.id in ('abort_if', 'zassert', 'Abort', 'abort'):
                candidates.extend(node.args[-1:])
        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'write' and ast.unparse(node.func.value) in ('sys.stdout', 'sys.stderr'):
            candidates.extend(node.args)
        candidates.extend(kw.value for kw in node.keywords if kw.arg in ('help', 'description', 'usage', 'epilog'))
        for candidate in candidates:
            for literal in literals(candidate):
                if id(literal) in seen:
                    continue
                seen.add(id(literal))
                specifiers = FORMAT.findall(literal.value) if id(literal) in formatted else []
                formats.append(specifiers)
                # The same tokens replace only static UI text in both versions.
                # Real formatting operands, labels stored in state, and data stay intact.
                literal.value = '<text:%d>' % len(formats) + ' '.join(specifiers)
    return tree, formats, bool(guides)


def run(path, args, source=None):
    if source is None:
        command = [sys.executable, '-X', 'utf8', str(path), *args]
    else:
        runner = "import sys; sys.argv=sys.argv[1:]; __file__=sys.argv[0]; exec(compile(sys.stdin.read(), __file__, 'exec'))"
        command = [sys.executable, '-X', 'utf8', '-c', runner, str(path), *args]
    return subprocess.run(command, input=source, cwd=path.parent, capture_output=True,
                          encoding='utf-8', timeout=20, env={**os.environ, 'PYTHONHASHSEED': '0'})


def main():
    files = sorted(path for path in ROOT.glob('*/*.py')
                   if path.parent.name != 'tests' and GUIDE.strip() in path.read_text(encoding='utf-8'))
    assert len(files) == 26, 'Expected all 26 localized Python 3 tools'
    originals = {}
    local = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        source = subprocess.check_output(['git', 'show', UPSTREAM + ':' + rel], cwd=ROOT).decode('utf-8')
        original_tree, original_formats, _ = normalized(source)
        local_tree, local_formats, has_guide = normalized(path.read_text(encoding='utf-8'))
        assert has_guide, rel
        assert original_formats == local_formats, (rel, 'Format operands changed')
        assert ast.dump(original_tree) == ast.dump(local_tree), (rel, 'Non-presentation logic changed')
        originals[rel] = ast.unparse(original_tree)
        local[rel] = ast.unparse(local_tree)
        help_result = run(path, ['-h'])
        assert help_result.returncode == 0 and '시드' in help_result.stdout, (rel, help_result.stderr)
    print('PASS: 26 source/format invariants and 26 Korean help screens', flush=True)

    base_args = {
        'cpu-intro/process-run.py': ['-l', '5:50,5:100'],
        'file-devices/process-run.py': ['-l', '5:50,5:100'],
        'file-implementation/vsfs.py': ['-n', '6'],
        'file-ffs/ffs.py': ['-f', 'in.example1', '-T', '-M'],
        'threads-intro/x86.py': ['-p', 'looping-race-nolock.s', '-a', 'bx=2', '-M', '2000', '-i', '2'],
        'threads-locks/x86.py': ['-p', 'test-and-set.s', '-a', 'bx=2', '-M', 'mutex,count', '-i', '3'],
        'cpu-sched-mlfq/mlfq.py': ['-l', '0,12,0:2,8,3', '-B', '10'],
        'file-ssd/ssd.py': ['-F', '-C', '-S'],
    }
    cases = []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        # This auxiliary generator invokes POSIX cat/gcc; help and AST are portable.
        if rel == 'cpu-api/generator.py':
            continue
        for suffix in ([], ['-c']):
            cases.append((rel, ['-s', '0'] + base_args.get(rel, []) + suffix, 0))
    for policy in ('FIFO', 'SJF', 'RR'):
        cases.append(('cpu-sched/scheduler.py', ['-l', '5,3,1', '-p', policy, '-q', '2', '-c'], 0))
    for policy in ('FIFO', 'LRU', 'MRU', 'OPT', 'UNOPT', 'RAND', 'CLOCK'):
        cases.append(('vm-beyondphys-policy/paging-policy.py', ['-a', '0,1,2,0,3,0,1', '-C', '3', '-p', policy, '-c'], 0))
    for level in ('0', '1', '4', '5'):
        cases.append(('file-raid/raid.py', ['-L', level, '-t', '-c'], 0))
    cases += [
        ('vm-mechanism/relocation.py', ['-p', '1'], 1),
        ('vm-segmentation/segmentation.py', ['-a', '0'], 1),
        ('threads-intro/x86.py', ['-p', 'loop.s', '-i', '0'], 1),
        ('file-ssd/ssd.py', ['-T', 'log', '-F', '-C', '-S', '-c'], 0),
        ('cpu-intro/process-run.py', ['-l', '5:50,5:100', '-c', '-p'], 0),
        ('cpu-sched-lottery/lottery.py', ['-s', '7', '-c'], 0),
        ('file-journaling/fsck.py', ['-s', '7', '-c'], 0),
        ('dist-afs/afs.py', ['-s', '7', '-c', '-d', '15'], 0),
    ]
    for rel, args, status in cases:
        path = ROOT / rel
        translated = run(path, args)
        assert translated.returncode == status, (rel, args, translated.stderr, translated.stdout[-500:])
        assert re.search('[가-힣]', translated.stdout), (rel, args, 'Missing Korean output')
        if status == 0:
            assert translated.stdout.count(GUIDE.strip()) == 1, (rel, args, 'Missing or duplicate reading guide')
        baseline = run(path, args, originals[rel])
        actual = run(path, args, local[rel])
        assert baseline.returncode == actual.returncode == status, (rel, args, baseline.stderr, actual.stderr)
        assert baseline.stdout == actual.stdout, (rel, args, 'Simulation output/data changed')
    print('PASS: %d execution scenarios; upstream data, order, and exit codes match' % len(cases))


if __name__ == '__main__':
    main()
