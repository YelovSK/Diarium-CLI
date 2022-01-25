# Diarium-CLI
## Configuration
Find the path of your `diary.db` file created by Diarium and put it in `config.json`.

Should be something like `C:/Users/<username>/AppData/Local/Packages/49297T.Partl.DailyDiary_jr9bq2af9farr/LocalState/diary.db`.

## Launch
`pip install -r requirements.txt` to install dependencies

`python JournalFind.py` from the root folder

## Usage
| Command | Description |
| :------: | :-------------------: |
| -h | shows this table
| -f `<word>` | searched for a word
| -fp `<word>` | searched for exact matches of a word
| -s `[number_of_top_words_showed]` | shows stats
| -c `<word>` | shows the number of occurrences of a word
| -d `<dd.mm.yy>` | shows a specific day
| -r | shows a random day
| -lang | percentage of english words
| -fol | creates a folder structure
| -fix | refreshes dictionary
| -update | updates journal files
| -clr | clears console
| -q | quit