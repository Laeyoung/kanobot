#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="kanobot-test"

echo "=== Building Docker image ==="
docker build -t "$IMAGE_NAME" .

echo ""
echo "=== Running 'kanobot onboard' ==="
docker run --name kanobot-test-run "$IMAGE_NAME" onboard

echo ""
echo "=== Running 'kanobot status' ==="
STATUS_OUTPUT=$(docker commit kanobot-test-run kanobot-test-onboarded > /dev/null && \
    docker run --rm kanobot-test-onboarded status 2>&1) || true

echo "$STATUS_OUTPUT"

echo ""
echo "=== Validating output ==="
PASS=true

check() {
    if echo "$STATUS_OUTPUT" | grep -q "$1"; then
        echo "  PASS: found '$1'"
    else
        echo "  FAIL: missing '$1'"
        PASS=false
    fi
}

check "kanobot Status"
check "Config:"
check "Workspace:"
check "Model:"
check "OpenRouter API:"
check "Anthropic API:"
check "OpenAI API:"

echo ""
if $PASS; then
    echo "=== All checks passed ==="
else
    echo "=== Some checks FAILED ==="
    exit 1
fi

# Cleanup
echo ""
echo "=== Cleanup ==="
docker rm -f kanobot-test-run 2>/dev/null || true
docker rmi -f kanobot-test-onboarded 2>/dev/null || true
docker rmi -f "$IMAGE_NAME" 2>/dev/null || true
echo "Done."
