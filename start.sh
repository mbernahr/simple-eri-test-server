#!/bin/bash
trap "kill 0" EXIT

echo "=================================================="
echo "   Change to the directory ‘rag-test’..."
echo "=================================================="

cd rag-test || { echo "Folder ‘rag-test’ not found!"; exit 1; }

echo "=================================================="
echo "   Start ERI backend (src/main.py)..."
echo "=================================================="

python src/main.py &

echo "Waiting 5 seconds for backend initialization..."
sleep 5

echo "=================================================="
echo "   Start frontend (frontend.py)..."
echo "=================================================="

python frontend.py

wait