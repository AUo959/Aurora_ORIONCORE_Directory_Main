# Archive Entropy Guard Report
Date: 2026-03-07
Workspace: /Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main

## Snapshot
- Total workspace size: **19G**
- Total files: **33,725**
- Archive files (`zip/7z/rar/tar/gz/...`): **1,236**
- Files over 100 MB: **52**
- Files over 500 MB: **6**
- Duplicate-name files in mirror folders (`Unzipped Archives`, `Complete Archive 4_19 copy`) and matching another copy elsewhere: **566 files / 7.20 GB**

## Top Oversized Artifacts (Current)
1. `Au_Archive_412_417/2.2.6b+Archives  2.zip` - 845 MB
2. `Au_Archive_412_417/2.2.6b+Archives .zip` - 845 MB
3. `ZIP_Archives/9c9ce296c28...2026-02-05...zip` - 503 MB
4. `Au_Archive_412_417/4:11:AuDev.zip` - 385 MB
5. `Aurora_Sim_Architecture/openai-cookbook-main.zip` - 333 MB

## Duplicate Filename Clusters (Highest Reclaim Potential)
- `GitHubDesktop-x64.zip`: 9 copies, 1,512.7 MB total, reclaimable if reduced to one copy: **1,344.6 MB**
- `2.2.6b+Archives  2.zip`: 2 copies, 1,690.3 MB total, reclaimable: **845.1 MB**
- `2.2.6b+Archives .zip`: 2 copies, 1,690.3 MB total, reclaimable: **845.1 MB**
- `GUI_Cloudhub.zip`: 4 copies, 757.5 MB total, reclaimable: **568.1 MB**
- `4:11:AuDev.zip`: 2 copies, 770.8 MB total, reclaimable: **385.4 MB**
- `AuroraMasterArchive.zip`: 3 copies, 423.1 MB total, reclaimable: **282.1 MB**
- `comprehensive_chat_archive.zip`: 3 copies, 272.1 MB total, reclaimable: **181.4 MB**

## Recommendations
### Keep
- Keep one canonical copy in primary archive roots: `ZIP_Archives/`, `Au_Archive_*`, `Aurora_Project_Cloudhub_Deploy/`.
- Keep the newest/active copy when filenames are identical and use mirrors only as cold backups.

### Archive (recommended first action)
- Move duplicate copies from `Unzipped Archives/` and `Complete Archive 4_19 copy/` into a dated staging folder for review.
- Expected immediate workspace cleanup candidate: up to **~7.2 GB** before final delete.

### Delete (only after staging review)
- Delete staged duplicates after checksum or manual spot-check confirms no unique payload differences.

## Safe Move Commands (non-destructive)
```bash
cd "/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main"
STAGE="$PWD/_entropy_staging/2026-03-07"
mkdir -p "$STAGE"

mv -nv "./Complete Archive 4_19 copy/2.2.6b+Archives .zip" "$STAGE/"
mv -nv "./Complete Archive 4_19 copy/2.2.6b+Archives  2.zip" "$STAGE/"
mv -nv "./Complete Archive 4_19 copy/4:11:AuDev.zip" "$STAGE/"
mv -nv "./Complete Archive 4_19 copy/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUI/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUI_Cloudhub/GUI_Cloudhub/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/GUI/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/GUI_Cloudhub/GUI_Cloudhub/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/Au_Archive_62_619/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/GUI_Cloudhub/GitHubDesktop-x64.zip" "$STAGE/"
mv -nv "./Complete Archive 4_19 copy/AuroraMasterArchive.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/Au_Archive_45_49/AuroraMasterArchive.zip" "$STAGE/"
mv -nv "./Complete Archive 4_19 copy/comprehensive_chat_archive.zip" "$STAGE/"
mv -nv "./Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/ZIP_Archives/comprehensive_chat_archive.zip" "$STAGE/"

# Review staged files before deletion
ls -lh "$STAGE" | sed -n '1,120p'

# Optional final purge (manual):
# rm -iv "$STAGE"/*
```

## Notes
- First run baseline established (no previous run memory).
- If desired, next run can compute growth deltas against this report.
