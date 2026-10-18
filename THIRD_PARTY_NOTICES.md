# Third-party notices

Virtual Pro Wrestling 64 Deluxe for PC (TanookiStudios/VPW64DeluxeRecomp) is built on the components
below. This is a fan-made program. It contains no game data: you supply your own ROM.

The port itself is licensed under the GNU General Public License v3.0 (see `LICENSE`), because its
symbol map and fixup tools began as jessetbh/VPW2Recomp, which is GPL-3.0.

| Component | What it is | License |
|---|---|---|
| [jessetbh/VPW2Recomp](https://github.com/jessetbh/VPW2Recomp) | the retail VPW2 function map and recompile fixup scripts (`syms/`, `tools/`) | GPL-3.0 |
| [jessetbh/N64ModernRuntime](https://github.com/jessetbh/N64ModernRuntime) (branch wcw) | the N64 runtime (threads, memory, saves, audio, RSP) | GPL-3.0 |
| [N64Recomp/N64Recomp](https://github.com/N64Recomp/N64Recomp) | the static recompiler that turns the ROM's code into C | MIT |
| [jessetbh/RecompFrontend](https://github.com/jessetbh/RecompFrontend) (branch wcw) | launcher, settings menu and controller input | MIT |
| [jessetbh/rt64](https://github.com/jessetbh/rt64) (branch wcw) | the renderer (Metal on Mac, Vulkan on Linux) | MIT |
| [RmlUi](https://github.com/mikke89/RmlUi), lunasvg, plutovg | the UI toolkit used by the launcher | MIT |
| [SDL2](https://libsdl.org) | window, input and audio | zlib |
| [FreeType](https://freetype.org) | font rendering for the launcher | FreeType License |
| [rcheevos](https://github.com/RetroAchievements/rcheevos) | RetroAchievements client (off unless enabled) | MIT |
| [PromptFont](https://shinmera.com/promptfont) | controller button glyphs in the menus | see `assets/promptfont/LICENSE.txt` |
| [Inter](https://rsms.me/inter/), [Noto Emoji](https://fonts.google.com/noto) | menu fonts | SIL Open Font License 1.1 |
| [SDL_GameControllerDB](https://github.com/mdqinc/SDL_GameControllerDB) | controller names and layouts (`recompcontrollerdb.txt`) | zlib |

## MIT License (N64Recomp, RecompFrontend, rt64, RmlUi, rcheevos)

```
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

Copyright holders: N64Recomp contributors (N64Recomp), Mr-Wiseguy and contributors (RecompFrontend),
RT64 contributors (rt64), Michael R. P. Ragazzon and contributors (RmlUi), RetroAchievements (rcheevos).

## GNU General Public License v3.0 (VPW2Recomp, N64ModernRuntime, this port)

The full text is in `LICENSE`.
