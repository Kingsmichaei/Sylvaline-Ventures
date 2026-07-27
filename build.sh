if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo "Activating virtual environment..."
  if [ -d "venv" ]; then
    source venv/bin/activate
  else
    echo "No virtual environment found. Please create one first."
    exit 1
  fi
fi