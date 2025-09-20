#!/bin/sh

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

/usr/bin/python3 -m ir_emitter "$input_file"
exit $?
    
  