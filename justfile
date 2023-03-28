# Compile client code
build: install_deps compile_elm

install_deps:
    poetry install --no-root

compile_elm:
    cd elm && elm make src/Main.elm --optimize --output=../aqimon/static/elm.js

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