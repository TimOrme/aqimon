# Compile client code
build:
     cd elm && elm make src/Main.elm --optimize --output=../aqimon/static/elm.js

# Lint code.
lint:
    black --check .
    ruff check .

# Format code
format:
    black .
    elm-format --yes elm/