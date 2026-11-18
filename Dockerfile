# Part 1: Build Elm Frontend
FROM node:26-slim AS elm-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install the Elm compiler
RUN npm install -g elm

WORKDIR /elm
COPY elm/elm.json ./
COPY elm/src ./src

# Compile Elm with --optimize and output directly to elm.js
RUN elm make src/Main.elm --optimize --output=elm.js

# Part 2: Build Python Backend
FROM python:3.15-slim

WORKDIR /app

# Copy package metadata and source code
COPY pyproject.toml .
COPY aqimon/ ./aqimon/
COPY --from=elm-builder /frontend/elm.js ./aqimon/static/elm.js

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Run the package entrypoint or module
CMD ["aqimon"]
