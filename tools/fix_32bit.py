#!/usr/bin/env python3
"""Fixes that only the 32-bit (armeabi-v7a) build needs. Never run for the 64-bit build.

Each fix replaces an exact piece of text and aborts if it is not found, so a changed upstream
shows up as a clear error in the 32-bit job only (the 64-bit APK is built by a separate job).
"""
import re
import sys
from pathlib import Path


def edit(path: Path, change) -> None:
    text = path.read_text(encoding="utf-8")
    new_text = change(text)
    if new_text == text:
        sys.exit(f"fix_32bit.py: nothing changed in {path}, upstream layout changed")
    path.write_text(new_text, encoding="utf-8")


def fix_atomic_ops(text: str) -> str:
    """The GCC/Clang branch uses `unsigned __int128`, which 32-bit targets do not have."""
    marker = "#else\n\n[[nodiscard]] inline bool AtomicCompareAndSwap(volatile u8* pointer"
    if marker not in text:
        sys.exit("fix_32bit.py: atomic_ops.h GCC branch not found")
    head, gcc = text.split(marker, 1)
    gcc = marker + gcc

    fallback = {
        "cas": '''[[nodiscard]] inline bool AtomicCompareAndSwap(volatile u64* pointer, u128 value, u128 expected) {
    // No native 128-bit atomics here. Only 64-bit guests use these, and the 3DS never does.
    std::scoped_lock lock{Atomic128FallbackMutex()};
    u128 current;
    std::memcpy(current.data(), const_cast<const u64*>(pointer), sizeof(u128));
    if (current != expected) {
        return false;
    }
    std::memcpy(const_cast<u64*>(pointer), value.data(), sizeof(u128));
    return true;
}
''',
        "cas_actual": '''[[nodiscard]] inline bool AtomicCompareAndSwap(volatile u64* pointer, u128 value, u128 expected,
                                               u128& actual) {
    std::scoped_lock lock{Atomic128FallbackMutex()};
    std::memcpy(actual.data(), const_cast<const u64*>(pointer), sizeof(u128));
    if (actual != expected) {
        return false;
    }
    std::memcpy(const_cast<u64*>(pointer), value.data(), sizeof(u128));
    return true;
}
''',
        "load": '''[[nodiscard]] inline u128 AtomicLoad128(volatile u64* pointer) {
    std::scoped_lock lock{Atomic128FallbackMutex()};
    u128 result;
    std::memcpy(result.data(), const_cast<const u64*>(pointer), sizeof(u128));
    return result;
}
''',
    }

    def wrap(source: str, signature: str, key: str) -> str:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 3
        original = source[start:end]
        if "__int128" not in original:
            sys.exit(f"fix_32bit.py: unexpected body for {key} in atomic_ops.h")
        replaced = f"#if defined(__SIZEOF_INT128__)\n{original}#else\n{fallback[key]}#endif\n"
        return source[:start] + replaced + source[end:]

    gcc = wrap(gcc, "[[nodiscard]] inline bool AtomicCompareAndSwap(volatile u64* pointer, u128 value, u128 expected) {", "cas")
    gcc = wrap(gcc, "[[nodiscard]] inline bool AtomicCompareAndSwap(volatile u64* pointer, u128 value, u128 expected,\n                                               u128& actual) {", "cas_actual")
    gcc = wrap(gcc, "[[nodiscard]] inline u128 AtomicLoad128(volatile u64* pointer) {", "load")

    helper = '''#if !defined(__SIZEOF_INT128__)
inline std::mutex& Atomic128FallbackMutex() {
    static std::mutex mutex;
    return mutex;
}
#endif

'''
    # The helper must live inside the GCC/Clang branch, right after its `#else`.
    gcc = gcc.replace("#else\n\n", "#else\n\n" + helper, 1)
    text = head + gcc
    return text.replace("#include <cstring>\n#endif", "#include <cstring>\n#include <mutex>\n#endif", 1)


def main(root: str) -> None:
    root_path = Path(root)
    src = root_path / "src"

    edit(src / "common" / "atomic_ops.h", fix_atomic_ops)

    # vulkan-hpp turns implicit vk::Handle <-> VkHandle conversions off on 32-bit targets, but the
    # renderer (and VMA calls) rely on them.
    def vulkan_conversion(text: str) -> str:
        anchor = "target_link_libraries(video_core PUBLIC citra_common citra_core)\n"
        if anchor not in text:
            sys.exit("fix_32bit.py: video_core link line not found")
        extra = (
            "\n# 32-bit: vulkan-hpp disables implicit handle conversions, but the code relies on them.\n"
            "if (NOT CMAKE_SIZEOF_VOID_P EQUAL 8)\n"
            "    target_compile_definitions(video_core PUBLIC VULKAN_HPP_TYPESAFE_CONVERSION=1)\n"
            "endif()\n"
        )
        return text.replace(anchor, anchor + extra, 1)

    edit(src / "video_core" / "CMakeLists.txt", vulkan_conversion)

    # `#ifdef` is always true for this macro, so 32-bit builds would offer custom GPU drivers
    # that adrenotools (64-bit only) cannot load.
    edit(
        src / "android" / "app" / "src" / "main" / "jni" / "native.cpp",
        lambda t: t.replace("#ifdef CITRA_ARCH_arm64\n", "#if CITRA_ARCH(arm64)\n", 1),
    )
    # sirit (the SPIR-V emitter) is always built with -Werror, -pedantic-errors and
    # -Wconversion/-Wsign-conversion. 32-bit targets trigger many more of those warnings, so
    # keep the warnings but stop them from failing the build.
    patched = 0
    for cmake in (root_path / "externals" / "sirit").rglob("CMakeLists.txt"):
        text = cmake.read_text(encoding="utf-8")
        new_text = (
            text.replace("        -pedantic-errors\n", "")
            .replace("        -Wfatal-errors\n", "")
            .replace("        -Wshadow\n        -Werror)", "        -Wshadow)")
        )
        if new_text != text:
            cmake.write_text(new_text, encoding="utf-8")
            patched += 1
    if patched == 0:
        sys.exit("fix_32bit.py: sirit warning flags not found, upstream layout changed")

    # More safety nets for the 32-bit build, passed to CMake:
    #  - SPIRV_WERROR=OFF: SPIRV-Tools is built with -Werror by default.
    #  - ENABLE_ASM=OFF: libressl would otherwise assemble its hand-written ARMv4 code, which only
    #    matters for the web service and is not worth a possible assembler failure.
    def cmake_args(text: str) -> str:
        old_arg = '                    "-DCITRA_WARNINGS_AS_ERRORS=OFF" // New compiler warnings must not break the build\n'
        if old_arg not in text:
            sys.exit("fix_32bit.py: CMake argument list not found in build.gradle.kts")
        new_arg = (
            '                    "-DCITRA_WARNINGS_AS_ERRORS=OFF", // New compiler warnings must not break the build\n'
            '                    "-DSPIRV_WERROR=OFF", // SPIRV-Tools: no -Werror\n'
            '                    "-DENABLE_ASM=OFF" // libressl: skip the ARM32 assembly\n'
        )
        return text.replace(old_arg, new_arg, 1)

    edit(root_path / "src" / "android" / "app" / "build.gradle.kts", cmake_args)
    print("== 32-bit fixes applied")


if __name__ == "__main__":
    main(sys.argv[1])
