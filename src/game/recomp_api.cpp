#include <algorithm>
#include <setjmp.h>
#include <cstdio>

#include "recomp.h"
#include "librecomp/helpers.hpp"
#include "ultramodern/ultramodern.hpp"
#include "ultramodern/config.hpp"
#include "recompui/recompui.h"

// Game-side runtime API callable from MIPS patches (adapted from BMHero's
// src/game/recomp_api.cpp). Every function here needs a matching address entry in
// patches/syms.ld and is exposed to patches via the generated manual_patch_symbols
// table — only implement (and list in syms.ld) what patches actually use.

#include "../ra/ra_client.h"

// Bridge for vpw2.toml `ignored` functions that aren't in N64Recomp's built-in
// auto-ignore set: toml-ignored calls are emitted against the PLAIN name, while
// librecomp exports only the `_recomp` shim.
extern "C" void osDriveRomInit_recomp(uint8_t* rdram, recomp_context* ctx);
extern "C" void osDriveRomInit(uint8_t* rdram, recomp_context* ctx) {
    // First boot-time hook that holds the rdram base: hand it to the
    // RetroAchievements prototype (no-op unless WCW_RA=1).
    wcw::ra::notify_rdram(rdram);
    osDriveRomInit_recomp(rdram, ctx);
}

extern "C" void recomp_puts(uint8_t* rdram, recomp_context* ctx) {
    PTR(char) cur_str = _arg<0, PTR(char)>(rdram, ctx);
    u32 length = _arg<1, u32>(rdram, ctx);

    for (u32 i = 0; i < length; i++) {
        fputc(MEM_B(i, (gpr)cur_str), stdout);
    }
    // Redirected stdout is fully buffered; without a flush, output sits in the CRT
    // buffer and is lost if the process is killed (this is a debugging API — flush).
    fflush(stdout);
}

extern "C" void recomp_exit(uint8_t* rdram, recomp_context* ctx) {
    ultramodern::quit();
}

// Aspect ratio the game should build its 3D projection with (widescreen patch,
// patches/widescreen.c). Same semantics as BMHero's: Original → the game's own ratio
// unchanged; Expand → the window's ratio, never below the original (RT64's Expand
// aspect mode then gives full-width perspective projections the wide viewport).
extern "C" void recomp_get_target_aspect_ratio(uint8_t* rdram, recomp_context* ctx) {
    float original = _arg<0, float>(rdram, ctx);
    const ultramodern::renderer::GraphicsConfig& config = ultramodern::renderer::get_graphics_config();

    if (config.ar_option == ultramodern::renderer::AspectRatio::Expand) {
        int width = 0, height = 0;
        recompui::get_window_size(width, height);
        if (width > 0 && height > 0) {
            _return(ctx, std::max(static_cast<float>(width) / height, original));
            return;
        }
    }
    _return(ctx, original);
}

// [wcw fix] Widescreen cull (aki-roadmap#47 / #5), called from the hand-edited func_800027F8
// (tools/readd_hand_edits.py). The game drops an object when its center is past
// |x| / (depth + 150) > 1.5 in view space, about 3.8x the 4:3 screen edge. In Expand the screen
// is wider, so large set pieces whose center is past that line but which reach into the extra
// width vanished at the edges. The horizontal limit is scaled by how much wider than 4:3 the
// screen is, keeping the game's own margin; 1 at Original, so 4:3 is unchanged.
extern "C" double wcw_widescreen_cull_scale() {
    const ultramodern::renderer::GraphicsConfig& config = ultramodern::renderer::get_graphics_config();
    if (config.ar_option != ultramodern::renderer::AspectRatio::Expand) {
        return 1.0;
    }

    int width = 0, height = 0;
    recompui::get_window_size(width, height);
    if (width <= 0 || height <= 0) {
        return 1.0;
    }

    return std::max(1.0, (static_cast<double>(width) / height) / (4.0 / 3.0));
}

// Non-local exit for the hack's text codec (see tools/hand_edits.py).
extern "C" jmp_buf vpw64dx_t9_exit;
jmp_buf vpw64dx_t9_exit;

// [vpw64dx] VPW_TRACE_LOOKUP=1: print every computed jump and the translated function it came from.
extern "C" void vpw_lookup_trace(const char* from, int32_t addr, int32_t s1, int32_t sp) {
    static const bool on = getenv("VPW_TRACE_LOOKUP") != nullptr;
    if (on) fprintf(stderr, "[lookup] %s -> 0x%08X s1=%08X sp=%08X\n", from, (uint32_t)addr, (uint32_t)s1, (uint32_t)sp);
}

// [vpw64dx] ring of the last hack-section pieces entered (tools/lastpiece.py), printed on a crash.
const char* vpw_last_piece[32] = {};
static uint32_t vpw_last_s0[32], vpw_last_sp[32];
static unsigned vpw_last_piece_i = 0;
extern "C" void vpw_note_piece(const char* name, uint32_t s0, uint32_t sp) {
    if (sp < 0x8008C000u || sp > 0x8008DE20u) return;   // bring-up: main thread's stack only
    unsigned k = vpw_last_piece_i++ & 31; vpw_last_piece[k] = name; vpw_last_s0[k] = s0; vpw_last_sp[k] = sp;
}
extern "C" void vpw_print_last_pieces() {
    fprintf(stderr, "[vpw64dx] last hack pieces (oldest first):");
    for (unsigned k = 0; k < 32; k++) { unsigned j = (vpw_last_piece_i + k) & 31; const char* n = vpw_last_piece[j]; if (n) fprintf(stderr, " %s(s0=%08X sp=%08X)", n, vpw_last_s0[j], vpw_last_sp[j]); }
    fprintf(stderr, "\n");
}
