#
# Assuming: you have python poetry installed
# sudo apt install python3-poetry
#
# if poetry install takes too long
# export PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring
#
# yt-dlp needs to be callable from path https://github.com/yt-dlp/yt-dlp/wiki/Installation
#
.PHONY: install installsysdeps
.PHONY: run
.PHONY: reformat
.PHONY: backfiles test test-min test-real

server:
	poetry run python main.py

# Assumptions:
#  - python black is in your path
# Black should use gitignore files to ignore refactoring
reformat:
	poetry run black src
	poetry run black utils
	poetry run black *.py

test:
	poetry run python -m unittest discover -s tests -v 2>&1 | tee test_output.txt
	rm test*.db
