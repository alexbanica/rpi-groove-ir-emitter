#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

while [ $# -gt 0 ]; do
    case $1 in
        --input)
            input_file="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$input_file" ]; then
    echo "Error: Input file not specified. Please use --input parameter."
    exit 1
fi

if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' does not exist."
    exit 1
fi

if [ ! -x "$VENV_PYTHON" ]; then
    (cd "$REPO_ROOT" && python3 -m venv .venv)
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment at $REPO_ROOT/.venv."
        exit 1
    fi

    (cd "$REPO_ROOT" && "$VENV_PYTHON" -m pip install .)
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install project into $REPO_ROOT/.venv."
        exit 1
    fi
fi

"$VENV_PYTHON" -m ir_emitter "$input_file"
exit $?
