# YASL Developer Contribution Guide

At this time YASL is a experimental project.
While it is intented to provide a valuable technical capibility, it is also a workspace to explore and refine developer workflows using GenAI coding assistants.
This project primarily uses GitHub Copilot with [instructions](./.github/copilot-instructions.md) intended to drive quality above quantity with GenAI contribution.
Additional Gemini 2.5 Pro is used for supporting research and concept exploration.

## Security Tools Setup

To run local security scans using `./ci.sh security`, you need to install CodeQL and Dependabot.

1.  **Create a local tools directory:**
    ```bash
    mkdir -p ~/local-tools/bin
    ```

2.  **Install CodeQL CLI:**
    *   Download the [CodeQL CLI bundle](https://github.com/github/codeql-cli-binaries/releases).
    *   Extract it to `~/local-tools/codeql`.
    *   Link the binary:
        ```bash
        ln -s ~/local-tools/codeql/codeql ~/local-tools/bin/codeql
        ```

3.  **Install Dependabot CLI:**
    *   Download the latest [Dependabot CLI release](https://github.com/dependabot/cli/releases).
    *   Extract it and move the `dependabot` binary to `~/local-tools/bin/dependabot`.
    *   Ensure it is executable: `chmod +x ~/local-tools/bin/dependabot`.

4.  **Container Runtime:**
    *   Dependabot requires a container runtime.
    *   If using **Podman**, ensure the socket is active:
        ```bash
        systemctl --user enable --now podman.socket
        ```
