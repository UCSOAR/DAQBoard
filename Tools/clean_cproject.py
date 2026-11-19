#!/usr/bin/env python3
"""
Cleans up the Eclipse/CubeIDE project files after CubeMX code generation.

CubeMX currently regenerates this project as if it were not "under root", which makes it
append a new, unused Debug/Release configuration pair to .cproject on every generation
(with wrong "../../" paths) instead of updating the existing ones. This script:

  1. Keeps only the first "Debug" and first "Release" configuration (the original ones,
     CubeMX always appends its duplicates after them) in .cproject and
     .settings/language.settings.xml, and removes every other configuration.
  2. Points the CMSIS-RTOS include paths of the kept configurations at whichever wrapper
     folder actually exists (CMSIS_RTOS for CMSIS_V1, CMSIS_RTOS_V2 for CMSIS_V2), so
     switching wrapper versions in the .ioc does not need manual include path edits.
  3. Removes include paths that became duplicates.

Edits are done on the text (not by re-serialising the XML) so the diff stays minimal.

Usage: python3 Tools/clean_cproject.py [--check]
  --check   Do not write anything, exit with 1 if the files would change.
"""
import re
import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CPROJECT = ROOT / ".cproject"
LANG_SETTINGS = ROOT / ".settings" / "language.settings.xml"
FREERTOS_SRC = ROOT / "Middlewares" / "Third_Party" / "FreeRTOS" / "Source"
KEEP_NAMES = ("Debug", "Release")


def find_blocks(text, tag, id_attr):
    """Return (start, end, id, name) for each top-level <tag ...>...</tag> block."""
    blocks = []
    for m in re.finditer(r"[ \t]*<%s\b[^>]*\b%s=\"([^\"]+)\"[^>]*>.*?</%s>[ \t]*\r?\n?" % (tag, id_attr, tag), text, re.S):
        name = re.search(r'\bname="([^"]+)"', m.group(0))
        blocks.append((m.start(), m.end(), m.group(1), name.group(1) if name else None))
    return blocks


def pick_kept_ids(blocks):
    kept = {}
    for _, _, cfg_id, name in blocks:
        if name in KEEP_NAMES and name not in kept:
            kept[name] = cfg_id
    return set(kept.values())


def remove_blocks(text, blocks, kept_ids):
    for start, end, cfg_id, _ in sorted(blocks, reverse=True):
        if cfg_id not in kept_ids:
            text = text[:start] + text[end:]
    return text


def remove_scanner_entries(text, kept_ids):
    def keep(m):
        cfg_id = m.group(1).split(";")[0]
        return m.group(0) if cfg_id in kept_ids else ""
    return re.sub(r"[ \t]*<scannerConfigBuildInfo instanceId=\"([^\"]+)\">.*?</scannerConfigBuildInfo>[ \t]*\r?\n?", keep, text, flags=re.S)


def fix_cmsis_paths(text):
    has_v1 = (FREERTOS_SRC / "CMSIS_RTOS").is_dir()
    has_v2 = (FREERTOS_SRC / "CMSIS_RTOS_V2").is_dir()
    if has_v1 == has_v2:
        return text  # Both or neither present, nothing sensible to do
    if has_v2:
        text = re.sub(r"(FreeRTOS/Source/CMSIS_RTOS)(?!_V2)", r"\1_V2", text)
    else:
        text = text.replace("FreeRTOS/Source/CMSIS_RTOS_V2", "FreeRTOS/Source/CMSIS_RTOS")
    return text


def dedupe_include_paths(text):
    """Remove repeated <listOptionValue> entries inside each <option> block."""
    def dedupe(m):
        seen, out = set(), []
        for line in m.group(0).splitlines(keepends=True):
            v = re.search(r'<listOptionValue\b[^>]*\bvalue="([^"]*)"', line)
            if v:
                if v.group(1) in seen:
                    continue
                seen.add(v.group(1))
            out.append(line)
        return "".join(out)
    # [^>]*(?<!/)> skips self-closing <option .../> tags so a block never spans two options
    return re.sub(r"<option\b[^>]*(?<!/)>.*?</option>", dedupe, text, flags=re.S)


def check_xml(text, path):
    try:
        xml.dom.minidom.parseString(text.encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        sys.exit(f"error: cleaning {path.name} produced invalid XML ({e}), nothing written")


def main():
    check_only = "--check" in sys.argv
    changed = []

    cproject = CPROJECT.read_text(encoding="utf-8")
    blocks = find_blocks(cproject, "cconfiguration", "id")
    kept_ids = pick_kept_ids(blocks)
    if len(kept_ids) != len(KEEP_NAMES):
        sys.exit(f"error: could not find both {KEEP_NAMES} configurations in .cproject, nothing written")

    new_cproject = remove_blocks(cproject, blocks, kept_ids)
    new_cproject = remove_scanner_entries(new_cproject, kept_ids)
    new_cproject = dedupe_include_paths(fix_cmsis_paths(new_cproject))
    check_xml(new_cproject, CPROJECT)
    if new_cproject != cproject:
        changed.append((CPROJECT, new_cproject, len(blocks) - len(kept_ids)))

    if LANG_SETTINGS.exists():
        lang = LANG_SETTINGS.read_text(encoding="utf-8")
        lang_blocks = find_blocks(lang, "configuration", "id")
        new_lang = remove_blocks(lang, lang_blocks, kept_ids)
        check_xml(new_lang, LANG_SETTINGS)
        if new_lang != lang:
            changed.append((LANG_SETTINGS, new_lang, len(lang_blocks) - len(kept_ids)))

    for path, content, removed in changed:
        rel = path.relative_to(ROOT)
        if check_only:
            print(f"{rel}: needs cleaning ({removed} extra configuration(s))")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"{rel}: cleaned ({removed} extra configuration(s) removed)")

    if check_only and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
