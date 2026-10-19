#!/usr/bin/env bash
# Installed locally on the Docker host; never downloaded/executed by CI.
set -euo pipefail
umask 077
fail() { echo "Deployment failed: $*" >&2; exit 1; }
[[ $# -le 1 ]] || fail 'expected at most one trusted configuration file'
config=${1:-/etc/gymms/deploy.conf}
[[ -f "$config" && ! -L "$config" ]] || fail 'missing trusted configuration'
[[ $(stat -c %u "$config") == "$EUID" ]] || fail 'configuration must belong to the invoking user'
config_mode=$(stat -c %a "$config")
(( (8#$config_mode & 022) == 0 )) || fail 'configuration must not be writable by group/others'
# This is administrator-controlled shell configuration, never remote release data.
source "$config"
: "${GYMMS_DEPLOY_PATH:?}" "${GYMMS_PROJECT_NAME:?}" "${GYMMS_GITHUB_REPOSITORY:?}"
: "${GYMMS_COMPOSE_FILE:?}" "${GYMMS_STATE_DIR:?}"
[[ "$GYMMS_DEPLOY_PATH" == /* && "$GYMMS_COMPOSE_FILE" == /* && "$GYMMS_STATE_DIR" == /* ]] || fail 'use absolute paths'
[[ "$GYMMS_GITHUB_REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail 'invalid GitHub repository'
[[ "$GYMMS_PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || fail 'invalid Compose project name'
cd -- "$GYMMS_DEPLOY_PATH"
[[ -f .env && -d media && -f "$GYMMS_COMPOSE_FILE" ]] || fail 'finish host setup before enabling CD'
mkdir -p "$GYMMS_STATE_DIR"
exec 9>"$GYMMS_STATE_DIR/deploy.lock"
flock -n 9 || fail 'another deployment is running'
[[ ! -e "$GYMMS_STATE_DIR/blocked" ]] || fail 'previous release needs recovery; inspect the blocked file'

repository="ghcr.io/${GYMMS_GITHUB_REPOSITORY,,}"
identity="https://github.com/$GYMMS_GITHUB_REPOSITORY/.github/workflows/ci-cd.yml@refs/heads/main"
# Resolve once, then verify and run that immutable digest even if the tag moves.
digest=$(docker buildx imagetools inspect "$repository:production" --format '{{json .Manifest}}' | jq -er '.digest')
[[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]] || fail 'registry returned an invalid digest'
image="$repository@$digest"
verification=$(cosign verify --certificate-identity "$identity" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  -a release=production "$image")
run_number=$(printf '%s' "$verification" | jq -er '[.[].optional.run_number | tonumber] | max')
[[ "$run_number" =~ ^[1-9][0-9]{0,8}$ ]] || fail 'signature has no valid release sequence'
previous_run=0
previous_image=unknown
if [[ -f "$GYMMS_STATE_DIR/current" ]]; then
  read -r previous_run previous_image < "$GYMMS_STATE_DIR/current"
  [[ "$previous_run" =~ ^[1-9][0-9]{0,8}$ ]] || fail 'invalid local release state'
  if [[ "$previous_image" == "$image" ]]; then
    echo "Already deployed $image"
    exit 0
  fi
  (( 10#$run_number > 10#$previous_run )) || fail 'refusing an older or replayed release'
fi
export GYMMS_IMAGE="$image"
compose=(docker compose --project-directory "$GYMMS_DEPLOY_PATH" \
  --project-name "$GYMMS_PROJECT_NAME" --env-file "$GYMMS_DEPLOY_PATH/.env" -f "$GYMMS_COMPOSE_FILE")
"${compose[@]}" config --quiet
# Download before downtime; database image/configuration is maintained by the host.
docker pull "$image"
"${compose[@]}" up -d --no-build --pull never --wait --wait-timeout 180 db
backup_dir="$(mktemp -d "$GYMMS_STATE_DIR/backup-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")"
printf '%s\n' "$previous_image" > "$backup_dir/previous-image"
printf '%s\n' "$image" > "$backup_dir/target-image"
printf '%s\n' "$image backups=$backup_dir" > "$GYMMS_STATE_DIR/blocked"
trap 'echo "Release interrupted; inspect $GYMMS_STATE_DIR/blocked and $backup_dir before resuming deployment." >&2' ERR
"${compose[@]}" stop web payment-worker
"${compose[@]}" exec -T db sh -ec \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$backup_dir/database.dump"
[[ -s "$backup_dir/database.dump" ]] || fail 'database backup is empty'
tar -czf "$backup_dir/media.tar.gz" media
"${compose[@]}" run --rm --no-deps --build=false --pull never -T initialize
"${compose[@]}" up -d --no-deps --no-build --pull never --force-recreate --wait --wait-timeout 180 web
"${compose[@]}" up -d --no-deps --no-build --pull never --force-recreate --wait --wait-timeout 180 payment-worker
"${compose[@]}" exec -T web python manage.py migrate --check
"${compose[@]}" exec -T web python manage.py check_readiness
state_tmp=$(mktemp "$GYMMS_STATE_DIR/current.XXXXXXXX")
printf '%s %s\n' "$run_number" "$image" > "$state_tmp"
mv -- "$state_tmp" "$GYMMS_STATE_DIR/current"
rm -- "$GYMMS_STATE_DIR/blocked"
trap - ERR
echo "Deployed $image; backups: $backup_dir"
