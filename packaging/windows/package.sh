#!/usr/bin/env bash
# Builds dist/ndc-native-windows/ (and dist/ndc-native-windows.zip): NDC Native.exe (the launcher,
# frozen with PyInstaller so players need no Python), Play NDC Native.exe, bb-probe.exe with the
# MSYS2 CLANG64 DLLs it needs, the preparation scripts and run.py. Run from an MSYS2 CLANG64
# shell after `bash build.sh`. Freezing uses a Windows Python 3.10+ (python.org; WINPYTHON
# overrides) and a private venv in out/pyenv with PyInstaller and Pillow.
set -euo pipefail
cd -- "$(dirname -- "$0")/../.."
source ./msys2-env.sh
[[ -f out/bb-probe.exe && -f out/bb-gpu-capabilities.exe && -f out/bb-play.exe ]] || { echo 'Build first: bash build.sh' >&2; exit 1; }

# A Windows Python (not MSYS2's) for PyInstaller.
python=${WINPYTHON:-}
if [[ -z $python ]]; then
    for candidate in /c/Python3*/python.exe "${LOCALAPPDATA:-/c/Users/$USER/AppData/Local}"/Programs/Python/Python3*/python.exe; do
        [[ -x $candidate ]] && python=$candidate
    done
fi
[[ -n $python ]] || { echo 'Need a Windows Python 3 (python.org) or WINPYTHON=path\to\python.exe' >&2; exit 1; }
# Windows Python needs USERPROFILE (some MSYS2 shells start without it).
export USERPROFILE=${USERPROFILE:-$(cygpath -w "/c/Users/$(id -un)")}
if [[ ! -x out/pyenv/Scripts/python.exe ]]; then
    "$python" -m venv out/pyenv
fi
out/pyenv/Scripts/python.exe -m pip install -q --disable-pip-version-check pyinstaller pillow
# The scripts run inside NDC Native.exe (--script): the standard modules they import come along.
hidden=()
for module in argparse base64 collections hashlib json re shutil struct tempfile zlib ctypes.wintypes \
              uncharted_art uncharted_fonts uncharted_widgets update_check bbport_steam PIL.ImageTk; do
    hidden+=(--hidden-import "$module")
done
out/pyenv/Scripts/python.exe -m PyInstaller --noconfirm --clean --log-level WARN --windowed \
    --name "NDC Native" --icon "$(cygpath -w "$PWD/launcher/uncharted.ico")" --distpath out/pyi-dist \
    --workpath out/pyi-work --specpath out/pyi-work --paths "$(cygpath -w "$PWD/scripts")" \
    --paths "$(cygpath -w "$PWD/launcher")" \
    --add-data "$(cygpath -w "$PWD/launcher/covers");covers" \
    "${hidden[@]}" \
    "$(cygpath -w "$PWD/launcher/uncharted_launcher.py")"

# The package is assembled in a fresh staging folder and zipped from there; dist/ndc-native-windows
# (a playable copy that may hold saves and settings) is only refreshed afterwards.
dest=out/stage/ndc-native-windows
rm -rf -- out/stage
mkdir -p "$dest/bin" "$dest/launcher" "$dest/scripts"
cp -r "out/pyi-dist/NDC Native/." "$dest/"
llvm-strip -o "$dest/Play NDC Native.exe" out/bb-play.exe
cp launcher/uncharted.ico launcher/uncharted.png "$dest/launcher/"
# The executables without debug information (out/ keeps the symbols for crash reports).
for exe in bb-probe.exe bb-gpu-capabilities.exe; do
    llvm-strip --strip-debug -o "$dest/bin/$exe" "out/$exe"
done
# Every DLL the executables load from the CLANG64 tree (SDL3, FFmpeg, Vulkan loader, ...).
ldd "$dest/bin/bb-probe.exe" "$dest/bin/bb-gpu-capabilities.exe" |
    awk '/\/clang64\/bin\// {print $3}' | sort -u | while read -r dll; do
        cp -u "$dll" "$dest/bin/"
    done
# Only what run.py runs to prepare a game (Bloodborne's patch and mod tools stay out).
cp scripts/prepare.py scripts/link_modules.py scripts/link_libc.py scripts/content_profile.py "$dest/scripts/"
cp run.py LICENSE "$dest/"
cp packaging/windows/README-Package.txt "$dest/README.txt"
# Licences (packaging/windows/THIRD-PARTY-NOTICES.txt explains the layout), and SOURCE.txt: the
# commit and library versions this package was built from (the GPL's source offer).
lic="$dest/licenses"
mkdir -p "$lic/msys2" "$lic/source" "$lic/python"
cp packaging/windows/THIRD-PARTY-NOTICES.txt "$lic/README.txt"
cp packaging/windows/licenses/*.txt "$lic/source/" 2>/dev/null || true
# FSR 4 (the v07 INT8 model) when its assets are in fsr4_shaders/ (tools/fetch_fsr4_assets.sh).
if [[ -d fsr4_shaders ]]; then cp -r fsr4_shaders "$dest/"; fi
# DLSS and DLSS Frame Generation (NVIDIA RTX): the MSVC-built bridge and NVIDIA's runtimes, next
# to bb-probe.exe (packaging/windows/build_dlss.sh). Without them those options stay unavailable.
if [[ -f out/bbport_dlss.dll && -f out/nvngx_dlss.dll ]]; then
    cp out/bbport_dlss.dll out/nvngx_dlss.dll "$dest/bin/"
    if [[ -f out/nvngx_dlssg.dll ]]; then cp out/nvngx_dlssg.dll "$dest/bin/"; fi
    cp out/NVIDIA-DLSS-LICENSE.txt "$lic/"
    cp gpu/dlss_bridge/LICENSE.txt "$lic/bbport_dlss-LICENSE.txt"
else
    echo "DLSS bridge not built (packaging/windows/build_dlss.sh): no DLSS in this package" >&2
fi
# Components built from source into bb-probe.exe.
for license in gpu/shadps4/LICENSE:shadPS4 gpu/third_party/imgui/LICENSE.txt:imgui \
               gpu/third_party/sirit/LICENSE.txt:sirit gpu/third_party/xbyak/COPYRIGHT:xbyak \
               gpu/third_party/magic_enum/LICENSE:magic_enum gpu/third_party/miniz/LICENSE:miniz \
               gpu/third_party/half/LICENSE.txt:half third_party/LibAtrac9/LICENSE:LibAtrac9 \
               gpu/third_party/fsr-vulkan/LICENSE.txt:FSR-Vulkan gpu/third_party/fonts/LICENSE-DejaVu.txt:DejaVu \
               gpu/third_party/wepoll/LICENSE:wepoll gpu/third_party/httplib/LICENSE:cpp-httplib; do
    if [[ -f ${license%%:*} ]]; then cp "${license%%:*}" "$lic/source/${license##*:}-LICENSE.txt"
    else echo "licence missing: ${license%%:*}" >&2; fi
done
# Every MSYS2 package that owns a shipped DLL (or is built in: VMA, SPIR-V headers), with its
# version for SOURCE.txt.
packages=$( { for dll in "$dest"/bin/*.dll; do pacman -Qqo "/clang64/bin/$(basename "$dll")" 2>/dev/null; done
              pacman -Qq mingw-w64-clang-x86_64-vulkan-memory-allocator mingw-w64-clang-x86_64-spirv-headers \
                         mingw-w64-clang-x86_64-boost mingw-w64-clang-x86_64-fmt 2>/dev/null; } | sort -u)
for package in $packages; do
    short=${package#mingw-w64-clang-x86_64-}
    if [[ -d /clang64/share/licenses/$short ]]; then cp -r "/clang64/share/licenses/$short" "$lic/msys2/"
    else echo "licence missing: MSYS2 package $package" >&2; fi
done
out/pyenv/Scripts/python.exe packaging/windows/collect_licenses.py "$(cygpath -w "$lic")"
{
    echo "Source of this package"
    echo "======================"
    echo
    echo "Program: GNU GPL v2 or later. Source: https://github.com/iannitram/uncharted_pc"
    echo "Commit:  $(git rev-parse HEAD)$(git diff --quiet --ignore-submodules=dirty HEAD -- . ':!dist' ':!out' || echo ' (with local changes)')"
    echo "Built:   $(date -u +%Y-%m-%d)"
    echo
    echo "Submodules (source in their own repositories, at these commits):"
    git submodule status --recursive | sed 's/^[ +-]/  /'
    echo
    echo "MSYS2 CLANG64 packages linked into or shipped with bb-probe.exe. Their exact sources are"
    echo "published by MSYS2: https://packages.msys2.org/ (search the package name; the source"
    echo "package of each version is linked there)."
    for package in $packages; do echo "  $(pacman -Q "$package")"; done
    echo
    echo "On request, the maintainer will provide the corresponding source of any GPL component"
    echo "of this package for three years from the build date, via the repository's issue tracker."
} > "$lic/SOURCE.txt"
find "$dest" -name __pycache__ -prune -exec rm -r {} +
mkdir -p dist
rm -f dist/ndc-native-windows.zip
(cd out/stage && powershell -NoProfile -Command \
    "Compress-Archive -Path ndc-native-windows -DestinationPath ../../dist/ndc-native-windows.zip")

# Refresh dist/ndc-native-windows, keeping what players create there (saves, settings), and only
# while nothing runs from it: deleting a running launcher's files breaks it.
play=dist/ndc-native-windows
running=$(powershell -NoProfile -Command \
    "@(Get-Process | Where-Object { \$_.Path -like '$(cygpath -w "$PWD/$play")\\*' }).Count" | tr -d '\r')
if [[ ${running:-0} != 0 ]]; then
    echo "dist/ndc-native-windows is in use ($running processes): not refreshed; the zip is ready." >&2
else
    mkdir -p "$play"
    find "$play" -mindepth 1 -maxdepth 1 ! -name user ! -name out ! -name art ! -name bbport.ini \
        ! -name input.ini ! -name last_run.log -exec rm -rf {} +
    cp -r "$dest/." "$play/"
fi
du -sh "$dest" dist/ndc-native-windows.zip
