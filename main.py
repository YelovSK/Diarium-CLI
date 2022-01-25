import os
import pathlib
import random
import re
import shelve
import shutil
import time
import sqlite3
import json
import helper as hp
from io import StringIO
from collections import Counter
from typing import List, Set
from rich.console import Console
from rich.table import Table
from rich.progress import track
from finder import Finder

class Journal:

    def __init__(self) -> None:
        self.console = Console()
        self.word_count_dict = {}
        self.check_file_count_mismatch()
        self.finder = Finder()

    def check_file_count_mismatch(self) -> None:
        if not os.path.exists(files_list_path):
            with open(files_list_path, "w") as f:
                f.write("-1")
        with open(files_list_path) as f:
            files_num = int(f.read())
        # files_num -> last checked number of files
        # len(hp.get_file_list()) -> number of files in the Diarium folder
        if files_num != len(hp.get_file_list()):
            self.console.print(f"File count mismatch (old: {files_num}, new: {len(hp.get_file_list())}), formatting...")
            self.write_dict()
            self.update_file_count()
        else:
            self.init_dict()

    def init_dict(self) -> None:
        try:
            self.read_dict()
        except (KeyError, FileNotFoundError):
            self.write_dict()

    def read_dict(self) -> None:
        with shelve.open(os.path.join(base, "shelve", "journal")) as jour:
            self.word_count_dict = jour["freq"]

    def write_dict(self) -> None:
        self.create_word_frequency()
        pathlib.Path(os.path.join(base, "shelve")).mkdir(parents=True, exist_ok=True)
        with shelve.open(os.path.join(base, "shelve", "journal")) as jour:
            jour["freq"] = self.word_count_dict

    def create_word_frequency(self) -> None:
        content = StringIO()
        for file in track(hp.get_file_list(), description="Reading files"):
            with open(os.path.join(path, file), encoding="utf-8") as f:
                content.write(f.read().lower())
        self.word_count_dict = Counter(re.findall(r"\w+", content.getvalue()))

    def update_diarium_files(self) -> None:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        dbfile = config["diary.db path"]
        con = sqlite3.connect(dbfile)
        entries = con.cursor().execute("SELECT Text, DiaryEntryId FROM Entries").fetchall()
        for text_raw, ticks in track(entries, description="Writing files"):
            text = hp.decode_entities(text_raw).replace("<p>", "").replace("</p>", "\n")
            date = hp.get_date_from_tick(int(ticks))
            with open(f"Diarium/Diarium_{date}.txt", "w", encoding="utf-8") as f:
                f.write(text)
        con.close()

    def get_years(self) -> Set[int]:
        # filename format -> Diarium_YYYY-MM-DD.txt
        YEAR_START_IX = 8
        YEAR_END_IX = YEAR_START_IX + 4
        return {int(file[YEAR_START_IX: YEAR_END_IX]) for file in hp.get_file_list()}

    def create_tree_folder_structure(self) -> None:
        self.create_year_and_month_folders()
        self.create_day_files()
        self.update_file_count()

    def create_year_and_month_folders(self) -> None:
        for year in [str(y) for y in self.get_years()]:
            if os.path.exists(os.path.join(base, year)):
                shutil.rmtree(os.path.join(base, year))
            for month in [str(m) for m in range(1, 12 + 1)]:
                pathlib.Path(os.path.join(year, month)).mkdir(parents=True, exist_ok=True)

    def create_day_files(self) -> None:
        for file in hp.get_file_list():
            with open(os.path.join(path, file), errors="ignore") as f:
                file_content = f.read()
            # filename format -> Diarium_YYYY-MM-DD.txt
            year, month, day = file.split("_")[1].split("-")
            # remove leading zeros
            month = month.lstrip("0")
            day = day.lstrip("0")
            with open(os.path.join(year, month, day), "w") as day_file:
                day_file.write(file_content)

    def update_file_count(self) -> None:
        with open(files_list_path, "w") as f:
            f.write(str(len(hp.get_file_list())))

    def get_most_frequent_words(self, count: int) -> list:
        return sorted(self.word_count_dict.items(), key=lambda item: item[1], reverse=True)[:count]

    def get_unique_word_count(self) -> int:
        return len(self.word_count_dict)

    def get_total_word_count(self) -> int:
        return sum(self.word_count_dict.values())

    def get_word_occurrences(self, word: str) -> int:
        return self.word_count_dict[word] if word in self.word_count_dict else 0

    def get_english_word_count(self) -> int:
        # not accurate cuz a word can be both Slovak and English and I don't have a database of Slovak words to compare
        english_words = set()
        with open(os.path.join("..", "text", "words_alpha.txt")) as f:
            for line in f:
                english_words.add(line.strip())
        return sum(count for word, count in self.word_count_dict.items() if word in english_words)
    
    def get_day_from_date(self, date: str) -> str:
        # date should be in the format DD.MM.YYYY
        try:
            d, m, y = date.split(".")
        except ValueError:
            return None
        file_path = f"Diarium/Diarium_{y}-{m}-{d}.txt"
        if not os.path.exists(file_path):
            return None
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    def get_random_day(self) -> str:
        random_file = random.choice(hp.get_file_list())
        with open(os.path.join(path, random_file), encoding="utf-8") as f:
            return hp.get_date_from_filename(random_file) + "\n" + f.read()
        
    def get_longest_day(self) -> str:
        words_in_file = {}  # file: word_count
        for file in hp.get_file_list(full_path=True):
            with open(file, encoding="utf-8") as f:
                words_in_file[file] = len(f.read().split())
        file, word_count = sorted(words_in_file.items(), key=lambda item: item[1])[-1]
        with open(file, encoding="utf-8") as f:
            return f"Word count: {word_count}\n\n{f.read()}"

    def create_help_table(self) -> Table:
        table = Table(title="Functions")
        for col in ("Command", "Description"):
            table.add_column(col)
        table.add_row("-h", "shows this table")
        table.add_row("-f <word>", "searches for a word")
        table.add_row("-fp <word>", "searches for exact matches of a word")
        table.add_row("-s (number_of_top_words_showed)", "shows stats")
        table.add_row("-c <word>", "shows the number of occurrences of a word")
        table.add_row("-d <dd.mm.yyyy>", "shows a specific day")
        table.add_row("-r", "shows a random day")
        table.add_row("-l", "shows the longest day")
        table.add_row("-lang", "percentage of english words")
        table.add_row("-fol", "creates a folder structure")
        table.add_row("-fix", "refreshes dictionary")
        table.add_row("-update", "updates journal files")
        table.add_row("-clr", "clears console")
        table.add_row("-q", "quit")
        return table

    def start(self) -> None:
        self.console.print("Type '-h' for help")
        table = self.create_help_table()
        while True:
            user_input = input(">> ")
            if len(user_input.split()) <= 1:
                action, val = user_input, ""
            else:
                action, val = user_input.split()[0], " ".join(user_input.split()[1:])
            if action == "-f":
                start = time.time()
                output = self.finder.find_and_get_output(word=val, exact_match=False)
                took_time = round(time.time() - start, 2)
                self.console.print(output)
                self.console.print(f"The word {val} was found {self.finder.get_current_occurrences()} times", highlight=False)
                self.console.print(f"Searched through {self.get_total_word_count()} words in {took_time}s",
                                   highlight=False)
            elif action == "-fp":
                self.console.print(self.finder.find_and_get_output(word=val, exact_match=True))
                self.console.print(f"The word {val} was found {self.finder.get_current_occurrences()} times", highlight=False)
            elif action == "-s":
                self.console.print("All words count:", self.get_total_word_count())
                self.console.print("Unique words count:", self.get_unique_word_count())
                if not val or not val.isnumeric():
                    val = 10
                self.console.print(self.get_most_frequent_words(int(val)))
            elif action == "-c":
                self.console.print(f"The exact match of word '{val}' was found {self.get_word_occurrences(val)} times")
                occurrences = self.finder.find_and_get_occurrences(word=val, exact_match=False)
                self.console.print(f"The number of all occurrences (incl. variations) is {occurrences}")
            elif action == "-d":
                file_content = self.get_day_from_date(date=val)
                if file_content is None:
                    self.console.print("File not found")
                else:
                    self.console.print(file_content)
            elif action == "-r":
                self.console.print(self.get_random_day())
            elif action == "-l":
                self.console.print(self.get_longest_day())
            elif action == "-lang":
                eng_word_count = self.get_english_word_count()
                self.console.print(f"All words: {self.get_total_word_count()} | English word count: {eng_word_count}")
                self.console.print(f"Percentage of english words: {round(eng_word_count * 100 / self.get_total_word_count(), 3)}%")
            elif action == "-fol":
                self.create_tree_folder_structure()
            elif action == "-h":
                self.console.print(table)
            elif action == "-fix":
                word_count_before = self.get_total_word_count()
                self.write_dict()
                self.update_file_count()
                word_count_after = self.get_total_word_count()
                if word_count_after - word_count_before == 0:
                    self.console.print("No new words found")
                else:
                    self.console.print(f"{word_count_after - word_count_before} words added to the dictionary")
            elif action == "-update":
                files_before = hp.get_file_list()
                self.update_diarium_files()
                files_after = hp.get_file_list()
                if files_after != files_before:
                    self.console.print(f"Added {len(files_after) - len(files_before)} day/s")
                    self.console.print("You should run '-fix' to update the dictionary")
                else:
                    self.console.print("No new entries found")
            elif action == "-clr":
                os.system("cls")
            elif action == "-q":
                break
            else:
                self.console.print("Command not recognized. Type '-h' for help.")


if __name__ == "__main__":
    with open("config.json") as cfg:
        config = json.load(cfg)
    base = os.getcwd()
    path = os.path.join(base, "Diarium")
    files_list_path = os.path.join(base, "files.txt")
    if not os.path.exists(path):
        os.makedirs(path)
    Journal().start()
