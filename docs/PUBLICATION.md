# Public source and local data

This repository publishes the editable SCAD, presets, simulator, part catalogue, build tools and selected numerical fixtures. Printable assets are distributed through GitHub Releases.

The root `.gitignore` uses an explicit source allowlist. Local exports, reference input, backups, logs, machine configuration, environment files, credentials, private keys, caches and the internal progress log stay outside Git tracking. Existing local files remain available on the original workstation.

Before each sync:

```powershell
git status --short
git diff --cached --stat
git ls-files
git diff --cached --check
```

Review both new filenames and file contents before committing. An ignore rule does not remove previously tracked data or earlier history. If a secret was published, revoke it at its issuer and remove it from both current files and reachable history before publishing further.

Run `python work/publication-audit.py` after staging the reviewed source files.
The audit checks the Git index and representative ignore rules; it does not
replace a history scan. With Gitleaks installed, check reachable history with:

```powershell
gitleaks git . --log-opts=--all --redact=100 --no-banner --report-format json --report-path work/publication/gitleaks.json
```

Keep audit reports, downloaded tools and history backups under ignored local
directories. Before rewriting published history, save and verify a Git bundle,
record remote ref hashes, and review the exact replacements. Update only the
affected refs with explicit leases, then scan a fresh clone. Normal public
syncs must fast-forward; do not overwrite unrelated remote work.

The initial publication started with a new Git repository and no existing remote for this project. Public commit identity uses GitHub's noreply address. Personal machine paths and internal run history are excluded from the initial source set.

Model reference: [MINI VAULT on MakerWorld](https://makerworld.com/en/models/968614-mini-vault), [author assembly video](https://www.youtube.com/watch?v=2BFG1QkyP0Q). The original model and instruction artwork belong to their respective authors; this repository does not assign a new license to those materials. Three.js retains its MIT notice in `simulator/vendor/THREE-LICENSE.txt`.
