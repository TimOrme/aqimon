# Compile client code
build: install_deps compile_elm

install_deps:
    poetry install --no-root

compile_elm:
    cd elm && elm make src/Main.elm --optimize --output=../aqimon/static/elm.js

# Lint code.
lint:
    black --check .
    ruff check .
    elm-format --validate elm/

# Format code
format:
    black .
    elm-format --yes elm/