# Diarium-CLI
Command-line interface providing random functions for the journaling app [Diarium](https://timopartl.com/).
## Configuration
Find the path of your `diary.db` file created by Diarium and put it in `config.json`.

Program will try to search for the file on launch if you're on Windows.

## Launch
`pip install -r requirements.txt` to install dependencies.

`python src/main.py` from the root folder.

## Usage
| Command | Description |
| :------: | :-------------------: |
| -h | shows this table
| -f `<word>` | searches for a word
| -fp `<word>` | searches for exact matches of a word
| -s `[number_of_top_words_showed]` | shows stats
| -c `<word>` | shows the number of occurrences of a word
| -d `<dd.mm.yyyy>` | shows a specific day
| -r | shows a random day
| -l | shows the longest day
| -lang | percentage of english words
| -fol | creates a folder structure
| -clr | clears console
| -q | quit