#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$script_dir"

prompt() {
  local reply reply_lower
  while true; do
    read -r -p "Build from GitHub (g) or use local image (l)? [g/l]: " reply
    reply_lower=$(printf '%s' "$reply" | tr '[:upper:]' '[:lower:]')
    case $reply_lower in
      g|github|"" ) echo "github"; return ;;
      l|local ) echo "local"; return ;;
      * ) echo "Please enter 'g' for GitHub or 'l' for local." ;;
    esac
  done
}

choice=$(prompt)

if [[ $choice == "github" ]]; then
  echo "Fetching latest commit from origin..."
  git fetch origin
  git_ref=$(git rev-parse origin/main)
  echo "Building fresh image from GitHub source at ${git_ref}..."
  docker compose build --no-cache --build-arg GIT_REF="$git_ref"
else
  echo "Using existing local image (no rebuild)."
fi

echo "Starting services..."
docker compose up -d
