# Compile client code
build: install_deps compile_elm

# Install dependencies for project
install_deps:
    poetry install --no-root

# Compile elm code for production
compile_elm:
    cd elm && elm make src/Main.elm --optimize --output=../aqimon/static/elm.js

# Compile elm code in development mode
compile_elm_dev:
    cd elm && elm make src/Main.elm  --output=../aqimon/static/elm.js

# Lint code.
lint:
    black --check .
    ruff check .
    mypy .
    elm-format --validate elm/

# Format code
format:
    black .
    elm-format --yes elm/

# Run tests
test:
    python -m pytest tests/