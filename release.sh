#!/usr/bin/env bash
# release_to_distribution.sh
# Release a tagged snapshot from internal (attx-engineering/warplink)
# to distribution (warpware-distribution/warplink) as a clean tree.

set -Eeuo pipefail

# ===== CONFIG DEFAULTS =====
DIST_URL_DEFAULT="git@github.com:warpware-distribution/warplink.git"
DIST_BRANCH_DEFAULT="main"
RELEASEIGNORE_FILE="../.releaseignore"   # patterns to remove from exported tree

# ===== UTILS =====
err()  { printf "\e[31mERROR:\e[0m %s\n" "$*" >&2; }
info() { printf "\e[34mINFO:\e[0m %s\n" "$*"; }
ok()   { printf "\e[32mOK:\e[0m %s\n" "$*"; }

cleanup() {
  if [[ -n "${TMPDIR_RELEASE:-}" && -d "$TMPDIR_RELEASE" ]]; then
    rm -rf "$TMPDIR_RELEASE"
  fi
}
trap cleanup EXIT

usage() {
  cat <<EOF
Usage:
  $0 --tag vX.Y.Z [--dist-url <git@...>] [--dist-branch <branch>] [--dry-run]

Options:
  --tag           REQUIRED. Tag name to release (created if missing).
  --dist-url      Distribution repo URL (default: ${DIST_URL_DEFAULT})
  --dist-branch   Distribution branch to update (default: ${DIST_BRANCH_DEFAULT})
  --dry-run       Build everything but skip the final push

Notes:
  - Optional ${RELEASEIGNORE_FILE} at repo root to exclude paths from export.
    Examples:
      .github/
      tests/**
      scripts/internal/**
      *.secret
EOF
}

# ===== ARG PARSE =====
TAG=""
DIST_URL="${DIST_URL_DEFAULT}"
DIST_BRANCH="${DIST_BRANCH_DEFAULT}"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag) TAG="${2:-}"; shift 2;;
    --dist-url) DIST_URL="${2:-}"; shift 2;;
    --dist-branch) DIST_BRANCH="${2:-}"; shift 2;;
    --dry-run) DRY_RUN="true"; shift;;
    -h|--help) usage; exit 0;;
    *) err "Unknown argument: $1"; usage; exit 1;;
  esac
done

[[ -n "$TAG" ]] || { err "--tag is required"; usage; exit 1; }

# ===== PRE-FLIGHT =====
# Make sure no weird env vars break git
unset GIT_DIR GIT_WORK_TREE

command -v git >/dev/null 2>&1 || { err "git not found"; exit 1; }
command -v tar >/dev/null 2>&1 || { err "tar not found"; exit 1; }
command -v rsync >/dev/null 2>&1 || { err "rsync not found; install with: sudo apt-get install -y rsync"; exit 1; }

# Ensure we're in the internal repo
git rev-parse --git-dir >/dev/null 2>&1 || { err "Run this inside the internal Git repo (attx-engineering/warplink)"; exit 1; }

# Make sure we can see the distribution repo
if ! git ls-remote --heads "${DIST_URL}" >/dev/null 2>&1; then
  err "Cannot access distribution repository: ${DIST_URL}
- Check your SSH agent/key and write permissions."
  exit 1
fi
ok "Distribution repo reachable"

# ===== VERIFY OR CREATE TAG IN INTERNAL REPO =====
if git rev-parse --verify --quiet "refs/tags/${TAG}" >/dev/null; then
  SOURCE_SHA="$(git rev-list -n1 "refs/tags/${TAG}")"
  info "Found existing tag '${TAG}' @ ${SOURCE_SHA}"
else
  info "Tag '${TAG}' not found — creating from latest 'main'."
  git fetch origin main --quiet || true
  git checkout -q main
  git pull -q origin main
  git tag -a "${TAG}" -m "Release ${TAG}"
  git push origin "${TAG}"
  SOURCE_SHA="$(git rev-list -n1 "refs/tags/${TAG}")"
  ok "Created tag '${TAG}' @ ${SOURCE_SHA}"
fi

info "Preparing release from tag '${TAG}'"

# ===== CREATE CLEAN EXPORT =====
TMPDIR_RELEASE="$(mktemp -d -t warplink_release_XXXXXX)"
EXPORT_DIR="${TMPDIR_RELEASE}/export"
mkdir -p "${EXPORT_DIR}"

info "Exporting clean tree via git archive..."
git archive --format=tar "${TAG}" | tar -x -C "${EXPORT_DIR}"
ok "Archive extracted to ${EXPORT_DIR}"

# ===== SANITIZE WITH .releaseignore =====
if [[ -f "${RELEASEIGNORE_FILE}" ]]; then
  info "Applying patterns from ${RELEASEIGNORE_FILE}"
  shopt -s dotglob globstar nullglob
  while IFS= read -r pattern || [[ -n "$pattern" ]]; do
    [[ -z "${pattern// }" || "${pattern}" =~ ^# ]] && continue
    matches=( "${EXPORT_DIR}"/${pattern} )
    if [[ ${#matches[@]} -gt 0 ]]; then
      for m in "${matches[@]}"; do
        rm -rf -- "$m"
        info "Removed: ${m#${EXPORT_DIR}/}"
      done
    fi
  done < "${RELEASEIGNORE_FILE}"
  shopt -u dotglob globstar nullglob
else
  info "No ${RELEASEIGNORE_FILE} found; skipping sanitize step"
fi

# ===== ADD RELEASE METADATA =====
DATE_ISO="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
cat > "${EXPORT_DIR}/RELEASE_METADATA.json" <<META
{
  "product": "warplink",
  "source_repo": "git@github.com:attx-engineering/warplink.git",
  "source_tag": "${TAG}",
  "source_commit": "${SOURCE_SHA}",
  "dist_repo": "${DIST_URL}",
  "dist_branch": "${DIST_BRANCH}",
  "released_at_utc": "${DATE_ISO}"
}
META
ok "Wrote RELEASE_METADATA.json"

# ===== INIT MINIMAL REPO & PUSH =====
PUSH_DIR="${TMPDIR_RELEASE}/warplink"
cd "${TMPDIR_RELEASE}"
git clone ${DIST_URL}
cd ${PUSH_DIR}

# Copy the exported tree
rm -rf "${EXPORT_DIR}/.git"
cp -r ../export/* .

# First commit
git add .
git commit -m "Release ${TAG} from ${SOURCE_SHA}"

# Create the same tag in the temp repo
git tag -a "${TAG}" -m "Release ${TAG}"

# Set remote
git remote add dist "${DIST_URL}"

info "About to push to ${DIST_URL} (branch: ${DIST_BRANCH}, tag: ${TAG})"
if [[ "${DRY_RUN}" == "true" ]]; then
  info "[DRY-RUN] Skipping push. To publish, rerun without --dry-run."
else
  # Fetch for force-with-lease safety (ok if branch doesn't exist yet)
  git fetch dist "${DIST_BRANCH}" || true
  git push dist "main:${DIST_BRANCH}" --force-with-lease
  git push dist "refs/tags/${TAG}:refs/tags/${TAG}"
  ok "Pushed branch '${DIST_BRANCH}' and tag '${TAG}' to distribution"
fi

ok "Release process completed"