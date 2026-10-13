"""Reject cached configure results that drop original native sources or flags."""
import hashlib
import json
from pathlib import Path
import re
import tarfile

with tarfile.open('/tmp/native-build-seed.tar.gz') as archive:
    original = archive.extractfile('./build.ninja').read().decode()
current = Path('/native-build/build.ninja').read_text()
pattern = r'^build CMakeFiles/_C_stable_libtorch\.dir/[^\n]+: (?:CUDA|CXX)_COMPILER[^\n]+\n(?:  [^\n]*\n)*'
old = re.findall(pattern, original, re.M)
new = re.findall(pattern, current, re.M)
assert len(old) == 109, len(old)
# CMake drops these Windows PDB output metadata fields when regenerating the
# same Linux Ninja build. Preserve comparison of every other field, including
# source rules, defines, includes, compile flags and dependency-file paths.
ignored_metadata = ('  TARGET_COMPILE_PDB = ', '  TARGET_PDB = ')
def canonical(block):
    return '\n'.join(line for line in block.splitlines()
                     if not line.startswith(ignored_metadata))
old = [canonical(x) for x in old]
new = [canonical(x) for x in new]
if old != new:
    old_by_rule = {x.splitlines()[0]: x.splitlines()[1:] for x in old}
    new_by_rule = {x.splitlines()[0]: x.splitlines()[1:] for x in new}
    diffs = []
    for rule in sorted(set(old_by_rule) & set(new_by_rule)):
        if old_by_rule[rule] != new_by_rule[rule]:
            diffs.append({'rule': rule,
                          'old_only_fields': sorted(set(old_by_rule[rule])-set(new_by_rule[rule])),
                          'new_only_fields': sorted(set(new_by_rule[rule])-set(old_by_rule[rule]))})
    print('NATIVE_BUILD_GRAPH_DIFFERENCE=' + json.dumps({
        'old_count': len(old), 'new_count': len(new),
        'missing_source_rules': sorted(set(old_by_rule)-set(new_by_rule))[:3],
        'extra_source_rules': sorted(set(new_by_rule)-set(old_by_rule))[:3],
        'changed_rules': len(diffs), 'field_differences': diffs[:2],
    }), flush=True)
assert old == new, {
    'original_object_rules': len(old), 'current_object_rules': len(new),
    'exact_rule_and_flag_match': False,
}
print('NATIVE_BUILD_GRAPH_GATE=' + json.dumps({
    'native_object_rules': len(new),
    'source_paths_defines_includes_and_flags_identical': True,
    'ignored_noncompiler_metadata': ['TARGET_COMPILE_PDB', 'TARGET_PDB'],
    'rules_sha256': hashlib.sha256(''.join(new).encode()).hexdigest(),
}), flush=True)
