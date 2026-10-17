# How the VPW64 Deluxe hack differs from retail VPW2, and how the map covers it

The port runs the fan hack "Virtual 64 Pro Wrestling Deluxe" (internal name `VPW64Delx`, game
code NA2J, 63.7 MB, SHA-1 `2ad9eb023a93f74c4f77e313a8bd583cec0c53d9`). It is built on the Japanese
Virtual Pro Wrestling 2 (32 MB retail). The function map in `syms/dump.toml` started as
jessetbh/VPW2Recomp's retail map; everything below is what the hack changed and what we did about it.

## Retail code is in place

- All four overlays and the fixed segment sit at the retail ROM offsets and RAM addresses
  (overlay descriptor table at rom 0x488C0 is byte-identical). 99.3% of the retail functions
  still end with the same `jr`/`j`, so the map transfers.
- About 60 retail functions were patched with code caves: a `j` to new code replaces two
  instructions, the new code does the original work plus the hack's, then jumps back. The
  recompile loop (`tools/recomp_loop.py`) adds a mid-function entry for each jump-back target.

## New code the hack added

| Where | Mapped as | Notes |
|---|---|---|
| vram 0x8000043C (20-byte gap after the entry stub) | `entry` section, `func_8000043C` | code cave for `func_80003E88` |
| rom 0x3A220–0x4BF40 (the fixed segment's data area, loaded by IPL3) | section `hack_main` | 17 functions found by `tools/find_hack_funcs.py` (recursive descent from every jump into the area) |
| rom 0x2FC6444 → RAM 0x8009FDD0, 0x320 bytes | section `hack_tramp` | 41 five-word trampolines in bss. The hack copies them there with CPU stores at boot, so no DMA names them: `register_overlays.cpp` maps the section at boot through the runtime's `recomp_load_extra_boot_overlays` hook. |
| rom 0x2F1A9D4 → RAM 0x801BB3A0, 0x1100 bytes (match-time code block) | section `hack_match` | Hack code in ovl_b (`func_8011E424`) allocates a 0x2100-byte heap buffer when a match starts, reads this block into it in 0x100-byte pieces and calls its first word; `0x8002C610` frees it after the match. Mapped by `tools/gen_far_section.py hack_match 0x2F1A9D4 0x801BB3A0 0x1100` and registered at boot like `hack_far`. The buffer address is assumed stable (it is the first allocation after the match overlays load). |
| rom 0x2FA1704 → RAM 0x80364B30, 0x25380 bytes (the hack's main code block) | section `hack_far` | The game reads it in 0x100-byte pieces at boot and calls its first word. Code reaches it through the pointer at 0x800559F0 (= 0x80368AF0, block + 0x3FC0): `lui/lw; addiu/addu; jr`. `tools/gen_far_section.py` maps every run of real instructions (data tables, strings and the zeroed area are left out) plus every computed-jump target (`tools/find_far_funcs.py`). Registered at boot with the trampolines. |

## Retail functions the hack rewrote in place (sizes corrected by `tools/hack_map_fixes.py`)

- `func_80003E88` is 0xC0 long now (0x80003F48–0x80003F64 is junk; code resumes at `func_80003F64`).
- `func_80009628` is 0x28 long (data follows, then `func_80009688`).
- `func_80030C5C` (retail 0x1D4) is now five helpers: 0x80030C5C/0x20, 0x80030C7C/0x2C, 0x80030CA8/0x8,
  0x80030D0C/0x1C, 0x80030D28/0x1C, 0x80030D44/0x1C, 0x80030D60/0x68, then a halfword table and floats.
- `func_8002BBF0` and `func_8002BD10` are data now (the hack reused dead libultra space); they stay stubbed.

## Hook chains that call the original code

Many hooks replace a retail function's first two instructions with `j <helper>`. The helper
chain usually ends in `j <retail address + 8>` (jump back = return). But some helpers *call*
the original: e.g. the text-id lookup `func_800E9EE8` → trampoline `0x800A00A0` → far
`0x803874D0` → `func_8003C5D0` → `func_8003C3F0` → `func_8002C560` → `j 0x800E9EF0` (the retail
body, which returns with `jr $ra`). Every hop must be mapped as code; `func_8003C5D0` was once
sized 0x4AC8 (running into data) and stubbed, which made the costume screen divide by zero.
`tools/noreturn_hooks.py` only turns a `jal helper` into `j` when the helper's final jump is the
call site's own return point; `0x8003C500` → `0x8003C588` → `j 0x80009F4C` jumps into a
*different* function's body and must stay a call, or the hook's stack frame is never popped.

## Saved-return-address idiom

Two hack routines keep the return address in a scratch register and jump back through it
(`move $t9,$ra` … `jr $t9` at 0x8000724C; `move $t8,$ra` … `jr $t8` at 0x80006C10). N64Recomp
never writes `$ra` on a call, so those jumps went to address 0. Both are patched to `jr $ra`
(a plain C return) by instruction patches in `vpw2.toml` (`tools/hack_map_fixes.py`).

## Recompiler settings

- Symbol-TOML mode (no ELF). `vpw2.toml` keeps the sister project's file name because every
  fixup script in `tools/` reads it; `vpw2.z64` is a link to `rom/vpw64deluxe.z64`.
- Audio microcode: unchanged from retail (rom 0x3A2F0, `rsp/vpw2_audio.toml`).
- `tools/regen.sh` runs the recompiler and every mandatory fixup until nothing is missing.
