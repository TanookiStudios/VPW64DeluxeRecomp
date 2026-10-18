#!/usr/bin/env python3
"""Fail loudly if a release folder (or this repo's tracked files) holds the game ROM, or
anything made from it.

    tools/release_scan.py <folder>        scan one package folder or app bundle
    tools/release_scan.py --tracked       scan every file git tracks in this repo
    tools/release_scan.py --self-test     prove the scan can fail

Checks: no ROM-type or save files, no generated C (RecompiledFuncs), no file equal to the
ROM, and no file containing any of several 32-byte samples cut from the ROM's code and data.
The ROM is read from rom/vpw64deluxe.z64 (never shipped); without it the scan refuses to pass."""
import hashlib, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, "rom", "vpw64deluxe.z64")
ROM_SHA1 = "2ad9eb023a93f74c4f77e313a8bd583cec0c53d9"
BAD_EXT = {".z64", ".n64", ".v64", ".rom", ".sav", ".sra", ".fla", ".eep", ".mpk", ".state"}
BAD_DIRS = {"RecompiledFuncs", "rom", "vendor", "build"}
SAMPLE_LEN = 32

def load_rom():
    if not os.path.isfile(ROM):
        sys.exit(f"release_scan: {ROM} not found; cannot prove the package is clean without the ROM to compare against")
    blob = open(ROM, "rb").read()
    if hashlib.sha1(blob).hexdigest() != ROM_SHA1:
        sys.exit("release_scan: rom/vpw64deluxe.z64 is not the expected ROM (SHA-1 mismatch)")
    samples = []
    for i in range(1, 16):
        base = len(blob) * i // 16
        for off in range(base, min(base + 65536, len(blob) - SAMPLE_LEN)):
            w = blob[off:off + SAMPLE_LEN]
            if len(set(w)) >= 20:
                samples.append(w); break
    if len(samples) < 10: sys.exit("release_scan: could not pick ROM samples")
    return blob, samples

def scan_files(paths, rom, samples):
    problems, nbytes = [], 0
    rom_sha = hashlib.sha256(rom).hexdigest()
    for path in paths:
        rel = os.path.relpath(path, ROOT) if path.startswith(ROOT) else path
        parts = set(rel.split(os.sep))
        if parts & BAD_DIRS and not rel.startswith("tools"): problems.append(f"{rel}: folder that never ships")
        if os.path.splitext(rel)[1].lower() in BAD_EXT: problems.append(f"{rel}: ROM or save file type")
        if rel.endswith((".c",)) and "RecompiledFuncs" in rel: problems.append(f"{rel}: generated code")
        try: data = open(path, "rb").read()
        except (IsADirectoryError, FileNotFoundError): continue
        nbytes += len(data)
        if hashlib.sha256(data).hexdigest() == rom_sha: problems.append(f"{rel}: is the ROM")
        for k, s in enumerate(samples):
            if s in data: problems.append(f"{rel}: contains ROM bytes (sample {k})"); break
    return problems, nbytes

def walk(folder):
    for d, _, files in os.walk(folder):
        for f in files: yield os.path.join(d, f)

def tracked():
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], capture_output=True, check=True).stdout
    return [os.path.join(ROOT, p.decode()) for p in out.split(b"\0") if p]

def self_test(rom, samples):
    with tempfile.TemporaryDirectory() as t:
        open(os.path.join(t, "ok.txt"), "wb").write(b"hello")
        p, _ = scan_files(list(walk(t)), rom, samples)
        if p: sys.exit("SELF-TEST FAILED: clean folder was flagged")
        open(os.path.join(t, "bad.bin"), "wb").write(b"x" * 100 + samples[3] + b"y" * 100)
        p, _ = scan_files(list(walk(t)), rom, samples)
        if not p: sys.exit("SELF-TEST FAILED: embedded ROM bytes not caught")
        os.remove(os.path.join(t, "bad.bin")); open(os.path.join(t, "game.z64"), "wb").write(b"z")
        p, _ = scan_files(list(walk(t)), rom, samples)
        if not p: sys.exit("SELF-TEST FAILED: ROM file type not caught")
    print("self-test passed: the scan catches ROM bytes and ROM-type files")

def main():
    rom, samples = load_rom()
    if sys.argv[1:] == ["--self-test"]: return self_test(rom, samples)
    if sys.argv[1:] == ["--tracked"]: paths, what = tracked(), "tracked files"
    elif len(sys.argv) == 2 and os.path.isdir(sys.argv[1]): paths, what = list(walk(sys.argv[1])), sys.argv[1]
    else: sys.exit(__doc__)
    problems, nbytes = scan_files(paths, rom, samples)
    if problems:
        print("ROM SAFETY SCAN FAILED, do not ship or push this:", file=sys.stderr)
        for p in problems: print("  " + p, file=sys.stderr)
        sys.exit(1)
    print(f"ROM safety scan passed: {what}, {len(paths)} files, {nbytes} bytes, {len(samples)} ROM samples")

if __name__ == "__main__": main()
