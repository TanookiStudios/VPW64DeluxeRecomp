#!/usr/bin/env bash
# Translate the ROM into C (RecompiledFuncs/) and run every mandatory fixup. Repeat until
# fix_backbranches and audit_coresidency report nothing missing. Never commit the output.
set -euo pipefail
cd "$(dirname "$0")/.."
for round in 1 2 3 4 5; do
    python3 tools/dedupe_names.py
    python3 tools/fix_delay_slots.py | tail -1
    rm -rf RecompiledFuncs
    python3 tools/recomp_loop.py | grep -v '^\[Info\]\|^  func_\|^\[Warn\]' | tail -3
    tail -c 8 RecompiledFuncs/funcs.h | grep -q endif || { echo 'recompiler output incomplete' >&2; exit 1; }
    python3 tools/fix_stumps.py | tail -1
    python3 tools/fix_switches.py > work/switches.log || true
    tail -1 work/switches.log
    python3 tools/fix_jraddend.py | tail -1
    python3 tools/fix_backbranches.py > work/backbranches.log || true
    tail -1 work/backbranches.log
    python3 tools/fix_selfentry.py | tail -1
    python3 tools/fix_zero_writes.py
    python3 tools/hand_edits.py
    python3 tools/add_coresidency_entries.py | tail -1
    # func_8000043C (the hack's entry-gap cave) branches into main_1050; N64Recomp already emits
    # a tail call there, fix_backbranches only audits within one section.
    missing=$(( $(grep MISSING work/backbranches.log | grep -vc "to 0x80003FAC " || true) + $(grep -c "^FAIL" work/switches.log || true) ))
    viol=$(python3 tools/audit_coresidency.py | tail -1 || true)
    echo "round $round: $missing missing mid-entries; $viol"
    if [ "$missing" = "0" ] && [ "$viol" = "0 violations" ]; then echo "regen complete"; exit 0; fi
    cat work/backbranches.log work/switches.log | grep "MISSING\|^FAIL" | python3 tools/apply_extra_funcs.py
done
echo "regen did not converge" >&2; exit 1
