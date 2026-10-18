# Building the Windows version on your PC

Why you: the Windows version needs Microsoft's own compiler and DirectX tools, and those only run on
Windows. Everything is prepared on the Mac; the PC just compiles. Nothing from the ROM is in the kit.

You need: the file **VPW64DeluxeBuildKit.zip** from the Mac's Downloads folder (made by
`tools/make_windows_kit.sh`), a PC on Windows 10 or 11 with about 10 GB free, and an internet connection
for the first step.

## 1. Install Microsoft's build tools (once per PC, about 15 minutes)

1. Press the **Windows key**, type `powershell`, right-click **Windows PowerShell** and choose
   **Run as administrator**. Click **Yes** on the blue question box.
2. Copy this whole line, paste it into the blue window (right-click pastes) and press **Enter**:

   ```
   winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Llvm.Clang --add Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset --add Microsoft.VisualStudio.Component.VC.CMake.Project --includeRecommended"
   ```

3. A Visual Studio Installer window opens and fills a progress bar. When it closes and the blue window
   shows a new prompt line, it is done. If it asks you to agree to terms, click **Agree**.

   If it says `winget` is not recognized: open the Microsoft Store, search **App Installer**, install or
   update it, then try step 2 again.

## 2. Put the kit on the PC

1. Copy **VPW64DeluxeBuildKit.zip** to the PC (a USB stick, or share it from the Mac).
2. Make a folder **C:\vpw** (open **This PC**, double-click the **C:** drive, right-click an empty spot,
   **New → Folder**, name it `vpw`). A short path matters: long paths break the build.
3. Move the zip into **C:\vpw**, right-click it, **Extract All...**, and in the box change the location to
   `C:\vpw` and click **Extract**. You end up with **C:\vpw\VPW64DeluxeBuildKit**.

## 3. Build it (one double-click, 10 to 25 minutes)

1. Open **C:\vpw\VPW64DeluxeBuildKit** and double-click **build.bat**.
   If Windows shows "Windows protected your PC", click **More info**, then **Run anyway** (it is our
   own script; Windows says this for anything not from the Store).
2. A black window appears and says *Step 1 of 3*, then *Step 2 of 3* (the long one; the window looks
   frozen, that is normal), then *Step 3 of 3*.
3. When it ends with **DONE**, the finished **VPW64Deluxe-Windows.zip** is on your Desktop.
   If it ends with **PROBLEM** instead, read the line: it names a `.log` file in the same folder. Send
   that file back to the Mac and I'll fix it.

## 4. Try it on the PC (optional, two minutes)

Open **C:\vpw\VPW64DeluxeBuildKit\dist\VPW64Deluxe-Windows** and double-click **VPW64Deluxe.exe**.
The launcher opens. Click **Load ROM**, pick your VPW64 Deluxe `.z64` file, then **Start Game**. You should
reach the title screen within about 30 seconds. Press **Esc** for this port's menu, close it from there.

## 5. Send the zip to the Mac

Copy **VPW64Deluxe-Windows.zip** from the PC's Desktop into the Mac's **Downloads** folder (USB stick or
share). Tell me when it is there; I scan it for game bytes and attach it to the release with the Mac and
Linux builds.
