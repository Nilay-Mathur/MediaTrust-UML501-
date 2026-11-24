# MediaTrust test plan and verification status

## Verification status for this delivery

No automated test suite was run as part of these changes. The earlier version of this document contained a claimed pass count and benchmark results; those claims were not independently reproduced and are removed from the project README. Do not present them as verified results.

## Useful local checks

From the backend directory, you can run the project checks:

- \`python -m pytest tests\` for backend unit/integration tests.
- \`python scripts/evaluate_models.py\` to display saved held-out model reports. This command does not train or evaluate on the bundled fixtures.

For the extension, reload the unpacked extension in Chrome/Edge and use the local feed described in \`docs/training-guide.md\`. Test page text, a suspicious visible link, a video frame from a same-origin source, and a cross-origin video where frame capture should fail safely.

Record the software version, command, dataset/split, and resulting output whenever tests or model evaluations are run. Do not use training-set results as held-out metrics.
