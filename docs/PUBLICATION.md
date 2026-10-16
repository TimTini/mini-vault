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

The initial publication started with a new Git repository and no existing remote for this project. Public commit identity uses GitHub's noreply address. Personal machine paths and internal run history are excluded from the initial source set.

Model reference: [MINI VAULT on MakerWorld](https://makerworld.com/en/models/968614-mini-vault), [author assembly video](https://www.youtube.com/watch?v=2BFG1QkyP0Q). The original model and instruction artwork belong to their respective authors; this repository does not assign a new license to those materials. Three.js retains its MIT notice in `simulator/vendor/THREE-LICENSE.txt`.
