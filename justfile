# Compile client code
build: install_deps compile_elm

# Install dependencies for project
install_deps:
    uv sync --no-install-project

# Compile elm code for production
compile_elm:
    cd elm && elm make src/Main.elm --optimize --output=../aqimon/static/elm.js

# Compile elm code in development mode
compile_elm_dev:
    cd elm && elm make src/Main.elm  --output=../aqimon/static/elm.js

# Lint code.
lint:
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy .
    elm-format --validate elm/

# Format code
format:
    uv run ruff format .
    elm-format --yes elm/

# Run tests
test:
    uv run pytest tests/