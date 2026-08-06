# FastHoppers IPA Archive Source

This repository converts the database used by Stuffed18's IPA Archive into an
AltStore-compatible `apps.json` source for apps such as KravaSigner.

## Your final KravaSigner URL

After uploading this repository and enabling GitHub Pages:

```text
https://FastHoppers.github.io/ipa-archive-source/apps.json
```

Repository names are case-insensitive in GitHub URLs, but use the exact lower-case
name `ipa-archive-source` to keep everything simple.

## Setup on iPhone

1. Open GitHub and sign into the `FastHoppers` account.
2. Create a new **public** repository named `ipa-archive-source`.
3. Upload every file and folder from this ZIP.
   - Make sure `.github/workflows/update-source.yml` is included.
4. Open the repository's **Actions** tab.
5. Enable workflows if GitHub asks.
6. Run **Update AltStore source** manually once.
7. Wait for the workflow to finish and create `apps.json`.
8. Go to **Settings → Pages**.
9. Under **Build and deployment**, choose:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/(root)**
10. Save and wait a minute or two.
11. Add this URL in KravaSigner:

```text
https://FastHoppers.github.io/ipa-archive-source/apps.json
```

## Important size warning

The Stuffed18 database is very large. A complete source may be too large for
KravaSigner to load smoothly.

To generate only the newest version of every app, edit the workflow line:

```yaml
run: python converter.py --output apps.json
```

to:

```yaml
run: python converter.py --latest-only --output apps.json
```

To test with only 100 apps:

```yaml
run: python converter.py --latest-only --max-apps 100 --output apps.json
```

## What the converter does

- Downloads `data/ipa.json` and `data/urls.json` from Stuffed18's repository.
- Groups records by bundle identifier.
- Converts each record to AltStore's app/version structure.
- Uses the archive's direct third-party IPA URLs.
- Regenerates the source daily through GitHub Actions.

## Notes

The source only indexes links already present in Stuffed18's project. The IPA
files are not copied into this repository. Availability, safety, ownership and
licensing of linked files are controlled by their original hosts.
