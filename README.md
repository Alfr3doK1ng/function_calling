## Requirement:

pip3 install macnotesapp

whisper.cpp

ollama with llama2 pulled and running in the background

## Run:

python3 main.py

## Misc:

If microphone can't be detected, try change `if (capture_id > 0) {` in common-sdl.cpp to `>=0`
