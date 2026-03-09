# Archive Entropy Guard Report
Date: 2026-03-07 (America/New_York)
Workspace: Aurora_ORIONCORE_Directory_Main (local workspace root)

## Executive Summary
- Archive files scanned: 1,238
- Total archive footprint: 12.78 GiB
- Files over 100 MiB (all types): 52
- Zero-byte archives: 2
- Largest growth zones by directory:
  - `Unzipped Archives`: 4.9G
  - `Complete Archive 4_19 copy`: 4.5G
  - `ZipWiz_Chamber_6_28`: 2.5G
  - `Au_Archive_412_417`: 2.1G
  - `ZIP_Archives`: 1.8G

## Oversized Artifacts (Top)
1. `886,188,338` bytes: `Complete Archive 4_19 copy/2.2.6b+Archives .zip`
2. `886,188,338` bytes: `Complete Archive 4_19 copy/2.2.6b+Archives  2.zip`
3. `886,188,338` bytes: `Au_Archive_412_417/2.2.6b+Archives .zip`
4. `886,188,338` bytes: `Au_Archive_412_417/2.2.6b+Archives  2.zip`
5. `708,461,869` bytes: `ZipWiz_Chamber_6_28/ZIPWIZ_Documents.zip`
6. `527,913,404` bytes: `ZIP_Archives/9c9ce296...-2026-02-05-...zip`
7. `504,494,062` bytes: `ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs2.zip`
8. `504,494,062` bytes: `ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs2 2.zip`
9. `404,114,667` bytes: `Complete Archive 4_19 copy/4:11:AuDev.zip`
10. `404,114,667` bytes: `Au_Archive_412_417/4:11:AuDev.zip`

## Duplicate Archive Families (Highest Reclaim Potential)
Potential reclaim is computed as `total family bytes - largest single member`.

1. `2.2.6b+archives` (4 files), reclaim ~2.48 GiB
2. `githubdesktop-x64` (9 files), reclaim ~1.31 GiB
3. `gumas+aur dev file archive` (12 files), reclaim ~0.56 GiB
4. `gui_cloudhub` (4 files), reclaim ~0.55 GiB
5. `zipwiz docs2` (2 files), reclaim ~0.47 GiB
6. `4:11:audev` (2 files), reclaim ~0.38 GiB
7. `auroramasterarchive` (6 files), reclaim ~0.34 GiB
8. `comprehensive_chat_archive` (3 files), reclaim ~0.18 GiB
9. `gui zip` (2 files), reclaim ~0.16 GiB
10. `aurora-cloudbank-symbolic-main` (11 files), reclaim ~0.09 GiB

## Binary Growth (Non-archive >100 MiB)
- `MicrosoftTeams.pkg` duplicated (2x at ~296.6 MiB each)
- `Stream_Deck_6.8.1.21263*.msi` duplicated (5x at ~240.1 MiB each)
- `sp155262.exe` duplicated (2x at ~174.9 MiB each)
- `Perplexity Setup 1.1.3.exe` duplicated (2x at ~162.8 MiB each)

## Keep / Archive / Delete Recommendations

### Keep (canonical copy)
- Keep heavy master bundles in archive roots rather than mirrored snapshots:
  - `Au_Archive_412_417/2.2.6b+Archives .zip`
  - `Au_Archive_412_417/2.2.6b+Archives  2.zip`
  - `Au_Archive_62_619/GitHubDesktop-x64.zip`
  - `Aurora_Project_Cloudhub_Deploy/GUI_Cloudhub.zip`
  - `Au_Archive_45_49/GUMAS+AUR Dev File Archive  4.zip`
  - `Au_Archive_45_49/GUMAS+AUR Dev File Archive  5.zip`
  - `Au_Archive_45_49/GUMAS+AUR Dev File Archive  6.zip`
  - `Au_Archive_45_49/AuroraMasterArchive.zip`
  - `ZIP_Archives/comprehensive_chat_archive.zip`
  - `ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs2.zip`

### Archive (move duplicates to quarantine first)
- Move duplicate mirrors under:
  - `Complete Archive 4_19 copy/`
  - `Unzipped Archives/Extra_Folders_Sort/...`
  - duplicate `ZIPWIZ Docs2 2.zip`
  - extra installer copies (`*.pkg`, `*.msi`, `*.exe`) outside a single canonical installer cache

### Delete (safe immediate)
- Zero-byte archives:
  - `Complete Archive 4_19 copy/exports/T1_replay_bundle_001.zip`
  - `Aurora_New_11_9/Aurora_New_11_9_BACKUP_2026-02-15.zip`

## Safe Move Commands (Non-destructive)
Use this exact sequence from repo root:

```bash
mkdir -p "_entropy_quarantine/2026-03-07"

mv -n "Complete Archive 4_19 copy/2.2.6b+Archives .zip" "_entropy_quarantine/2026-03-07/"
mv -n "Complete Archive 4_19 copy/2.2.6b+Archives  2.zip" "_entropy_quarantine/2026-03-07/"

mv -n "Complete Archive 4_19 copy/GitHubDesktop-x64.zip" "_entropy_quarantine/2026-03-07/"
mv -n "GUI_Cloudhub/GitHubDesktop-x64.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUI/GitHubDesktop-x64.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUI_Cloudhub/GUI_Cloudhub/GitHubDesktop-x64.zip" "_entropy_quarantine/2026-03-07/"

mv -n "Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/GUI_Cloudhub.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/Au_Archive_62_619/GUI_Cloudhub.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Au_Archive_62_619/GUI_Cloudhub.zip" "_entropy_quarantine/2026-03-07/"

mv -n "Complete Archive 4_19 copy/GUMAS+AUR Dev File Archive  4.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Complete Archive 4_19 copy/GUMAS+AUR Dev File Archive  5.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Complete Archive 4_19 copy/GUMAS+AUR Dev File Archive  6.zip" "_entropy_quarantine/2026-03-07/"

mv -n "Complete Archive 4_19 copy/AuroraMasterArchive.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/Au_Archive_45_49/AuroraMasterArchive.zip" "_entropy_quarantine/2026-03-07/"

mv -n "Complete Archive 4_19 copy/comprehensive_chat_archive.zip" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/ZIP_Archives/comprehensive_chat_archive.zip" "_entropy_quarantine/2026-03-07/"

mv -n "ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs2 2.zip" "_entropy_quarantine/2026-03-07/"

mv -n "Complete Archive 4_19 copy/MicrosoftTeams.pkg" "_entropy_quarantine/2026-03-07/"
mv -n "ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs2/Stream_Deck_6.8.1.21263(1).msi" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/Stream_Deck_6.8.1.21263(1).msi" "_entropy_quarantine/2026-03-07/"
mv -n "Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/Stream_Deck_6.8.1.21263(2).msi" "_entropy_quarantine/2026-03-07/"
```

## Optional hard-delete commands (run only after validation)
```bash
rm -f "Complete Archive 4_19 copy/exports/T1_replay_bundle_001.zip"
rm -f "Aurora_New_11_9/Aurora_New_11_9_BACKUP_2026-02-15.zip"
```

## Notes
- No destructive action was executed during this run.
- Recommendations are path- and size-based heuristics. For exact-content dedupe, run hash checks on candidate sets before permanent deletion.
