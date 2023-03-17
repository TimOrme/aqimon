# Compile client code
build:
     cd elm && elm make src/Main.elm --optimize --output=../aqimon/static/elm.js
