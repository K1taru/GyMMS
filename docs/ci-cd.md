# Signed images with outbound-only deployment

PRs targeting `main` build and test the application on GitHub-hosted runners. A merge into `main` runs those checks, builds AMD64 and ARM64 images, then tests both published candidates by digest. Only after the candidate tests pass does the `production` job sign the image index using GitHub's short-lived OIDC identity and promote it to `ghcr.io/k1taru/gymms:production`. Third-party actions are pinned to full commit hashes.

A systemd timer on the Pi checks the registry approximately every three minutes after the previous deployment check finishes, with up to 30 seconds of random delay and systemd timer accuracy affecting the actual schedule. It verifies the signature against this exact workflow on `main`, resolves the image to its immutable digest, downloads it, backs up PostgreSQL/media, migrates, recreates web/worker, and checks readiness. The host runs administrator-installed scripts and Compose configuration. It never downloads shell scripts or Compose changes from a release. There is no incoming deployment connection, production SSH key in GitHub, or GitHub runner on the Pi.

## GitHub setup

1. Enable Actions and allow this repository to publish GitHub Container Registry packages using `GITHUB_TOKEN`. No manually created registry write token or signing key is needed in GitHub. A pre-existing package must grant this repository Actions access.
2. Create the `production` environment and restrict it to branch `main`. Require PRs and the **Build and test** status check in a `main` ruleset. Protect changes to `.github/workflows/` with review. Leave deployment reviewers off to keep the requested automatic releases; enabling reviewers adds a manual gate before image publication. Environment features depend on the repository visibility and GitHub plan.
3. Merge the workflow into `main`. The package is named after the lowercased repository slug. Keep the package private unless you deliberately want public image access; the workflow does not change package visibility. Keyless signing records signing metadata in Sigstore's public transparency service, including the image identity/digest; application secrets are not included.
4. If the repository is renamed, update the host's `GYMMS_GITHUB_REPOSITORY` after reviewing the new workflow identity. The configured case must match the GitHub repository identity (`K1taru/GyMMS`).

PR jobs cannot publish or sign images. Successful publication means an approved candidate is available; actual host deployment status is reported by systemd on the Pi, not by the GitHub job. A failed publication leaves the previous production tag in place.

## Prepare the Pi once

This is for an already working PostgreSQL 18 installation. Complete the [first setup](setup.md#first-setup) and any [PostgreSQL cutover](docker.md#cutover-from-postgresql-16) manually before enabling automatic releases. Keep the existing Compose project name, data volume, `.env`, and uploads. Never use `down -v` for this setup.

Install Docker Engine, Compose v2, Docker Buildx, Bash, `flock` (util-linux), jq, tar, and Cosign v3. Use the official [Cosign installation instructions](https://docs.sigstore.dev/cosign/system_config/installation/), verifying the release binary before installing it. Install tools globally, such as `/usr/local/bin/cosign`; tools installed only inside a user's home will be inaccessible to the systemd service. No build/emulation tools beyond Buildx's registry inspection are used on the Pi.

The configured Pi installation is `/home/k1taru/srv/GyMMS`, with Compose project name `gymms`. Its PostgreSQL 18 volume is `gymms_postgres18_data`, mounted at `/var/lib/postgresql`. Keep the existing `.env`, `media/`, project name, and database volume in place. The service uses `ProtectHome=read-only` so it can read this installation and back up uploads. Docker itself manages writes to the containers' mounts. For another host, set the deployment path and project name to that host's existing installation. Do not start a second project against an empty database.

On a Debian-based Pi, the dependencies installed during setup were:

```bash
sudo apt update
sudo apt install -y jq golang-go
GYMMS_TOOL_DIR=$(mktemp -d)
GOBIN="$GYMMS_TOOL_DIR" go install github.com/sigstore/cosign/v3/cmd/cosign@latest
sudo install -o root -g root -m 0755 "$GYMMS_TOOL_DIR/cosign" /usr/local/bin/cosign
cosign version
jq --version
```

Continue only if compilation and installation succeed. The verified installation reported Cosign v3.1.3 on linux/arm64 and jq 1.7; the command above follows the latest v3 release.

Run the following from a reviewed checkout on the Pi. These commands install fixed host configuration; they do not launch a release. If the timer was already enabled, stop it with `sudo systemctl stop gymms-cd-ci.timer` while completing setup. On subsequent installations, review existing `/etc/gymms/deploy.conf` and `/etc/gymms/compose.yml` before replacing them:

```bash
sudo install -d -o root -g root -m 0700 /etc/gymms /var/lib/gymms-deploy /var/lib/gymms-deploy/docker
sudo install -o root -g root -m 0755 scripts/deploy.sh /usr/local/sbin/gymms-deploy
sudo install -o root -g root -m 0600 deploy/deploy.conf.example /etc/gymms/deploy.conf
sudo install -o root -g root -m 0600 docker-compose.yml /etc/gymms/compose.yml
sudo install -o root -g root -m 0644 deploy/gymms-cd-ci.service deploy/gymms-cd-ci.timer /etc/systemd/system/
sudoedit /etc/gymms/deploy.conf
```

Set `GYMMS_DEPLOY_PATH` and `GYMMS_PROJECT_NAME` to the existing installation. The remaining defaults should work for this repository. The Compose file must include the `GYMMS_IMAGE` variable added in this change. Keep the installed script/configuration/Compose file writable only by administrators. Keep the application `.env` private; CI does not need its values. The root service can access Docker and read media for backups. Its systemd restrictions provide defense in depth; Docker socket access remains equivalent to substantial host control.

For a private GHCR package, open [GitHub Tokens (classic)](https://github.com/settings/tokens), select **Generate new token (classic)**, name it `raspy-gymms-pull`, choose an expiration, and select **read:packages** only (plus organization authorization if required). Replace the token before it expires. The token's account must have access to the package. Store it only in the Pi's Docker credential configuration, not in this repository or GitHub Actions secrets:

```bash
sudo docker --config /var/lib/gymms-deploy/docker login ghcr.io --username YOUR_GITHUB_USER
```

Paste the token, rather than the GitHub password, at the password prompt. The credential file is private but Docker's default credential file is not encrypted; a compatible credential helper can improve storage. For a public package this login is unnecessary. Cosign and Buildx use the same `DOCKER_CONFIG` as Docker.

Confirm that a production image has been published and is accessible before starting deployment:

```bash
sudo docker --config /var/lib/gymms-deploy/docker \
  buildx imagetools inspect ghcr.io/k1taru/gymms:production
```

If login succeeds but inspection reports `not found`, check the CI / CD run on `main` in GitHub Actions. **Publish signed production image** must succeed; PR checks deliberately skip publication. Merge the reviewed PR into `main`, or manually dispatch the workflow on `main` if needed. A successful login alone does not establish that the tag exists or that the account has package access. Keep the timer stopped until inspection succeeds.

An existing `docker-gymms.service` that runs `docker compose up -d --build` also needs a reviewed boot configuration before enabling automatic deployment. It can otherwise replace the released image with a local build on reboot. Removing `--build` alone is insufficient because Compose defaults to `gymms-app:local`; boot must select the recorded production digest and the installed Compose configuration. This boot-service transition has not yet been applied on the Pi. Do not disable it with `--now` during setup: its existing `ExecStop` runs `docker compose down`.

Verify the required tools and the existing PostgreSQL image are available before enabling the timer:

```bash
docker compose version
docker buildx version
cosign version
jq --version
docker image inspect postgres:18.6-trixie --format '{{.Architecture}}'
```

The agent deliberately does not pull or upgrade PostgreSQL. Database image/configuration changes require administrator review. Image downloads, signature verification, and Sigstore trust initialization need outbound HTTPS/DNS access to GHCR, GitHub's package infrastructure, and Sigstore's services. No inbound port forwarding is required. Keep the existing app tunnel and database network restrictions.

## First release and normal operation

Once GitHub has published a signed production image, run one supervised deployment before enabling the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl start gymms-cd-ci.service
sudo journalctl -u gymms-cd-ci.service -n 80 --no-pager
sudo cat /var/lib/gymms-deploy/current
```

Confirm login, uploads, receipts, and worker behavior, then enable automatic polling:

```bash
sudo systemctl enable --now gymms-cd-ci.timer
systemctl list-timers gymms-cd-ci.timer
```

Each release has a short downtime window while web/worker stop for backup and migration. Worker startup confirms a running process, not PayMongo connectivity. Unchanged image digests are skipped. The agent rejects a different digest with an older/equal signed workflow run number, preventing ordinary replay after a successful deployment. Keep the state file; losing it also loses this replay history. To roll back code, merge a reviewed revert so a new workflow run produces a new signed release. Signatures establish origin and integrity; they do not prove the application code is harmless or prevent a compromised authorized GitHub workflow from publishing malicious code.

Backups live under `/var/lib/gymms-deploy/backup-<UTC timestamp>-<unique suffix>/` and contain `database.dump`, `media.tar.gz`, and previous/target image references. The first release's previous image is recorded as `unknown`; record the old local image and deployment settings before the first run if you need an immediate rollback route. Provision disk space, test restores, copy backups off-host, and manage retention. The agent does not prune images, volumes, or backups.

Use the installed Compose file and exact image digest for production maintenance. The Git checkout's default `gymms-app:local` is intended for development/manual builds. Running the [setup guide's manual build/up commands](setup.md#routine-maintenance) against a timer-managed production project could select a different image. Read the current reference from `/var/lib/gymms-deploy/current` (second field), set `GYMMS_IMAGE` to it, and use the configured project name/directory and `/etc/gymms/compose.yml` for operational commands. Avoid environment overrides that change Docker/Compose targets.

The host's Compose file, script, database pin, and systemd units are updated manually after reviewing repository changes. Automatic releases update application code and committed migrations inside the image; they do not automatically change host ports, mounts, database version, or privileges.

## Failure and recovery

If signature validation, registry access, image download, or preflight fails, applications keep running. The next timer invocation may retry. If a failure or interruption occurs after the agent creates `/var/lib/gymms-deploy/blocked`, automatic releases remain blocked, including newer releases, until an administrator handles recovery. This prevents repeated migrations/restarts after a partially applied release. A backup may be incomplete if its creation failed.

```bash
sudo systemctl stop gymms-cd-ci.timer
sudo journalctl -u gymms-cd-ci.service -n 100 --no-pager
sudo cat /var/lib/gymms-deploy/blocked
```

Inspect the backup and containers using the recorded target image and the installed Compose configuration. A timeout/disconnect can leave Docker-managed migration containers running; inspect them before trying again. Prefer a forward fix. Database rollback requires a planned restore and payment reconciliation; see [Docker recovery](docker.md#recovery-and-routine-releases). Do not reopen an old app against a changed schema without checking compatibility.

After the underlying issue is corrected and the intended recovery/retry is reviewed, remove only the block marker and run the service once:

```bash
sudo rm -- /var/lib/gymms-deploy/blocked
sudo systemctl start gymms-cd-ci.service
sudo journalctl -u gymms-cd-ci.service -n 80 --no-pager
sudo systemctl start gymms-cd-ci.timer
```

Configure host monitoring to alert on failed `gymms-cd-ci.service` runs; the outbound deployment does not report success/failure back to GitHub. To stop automatic releases, stop/disable the timer. If you previously configured deployment SSH secrets, remove those unused secrets and revoke the dedicated deployment key after confirming the timer works. Administrative SSH access can remain governed by your normal host policy.

Implementation references: [Docker multi-platform CI](https://docs.docker.com/build/ci/github-actions/multi-platform/), [Sigstore identity verification](https://docs.sigstore.dev/cosign/verifying/verify/), and [GitHub deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments).
