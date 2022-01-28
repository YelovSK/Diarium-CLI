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
from collections import Counter
from typing import List, Set
from rich.console import Console
from rich.table import Table
from rich.progress import track
from finder import Finder


class Journal:

    def __init__(self) -> None:
        self.console = Console()
        self.word_count_map = {}
        self.entries_map = {}
        self.init_dict()
        self.check_for_new_files()

    def init_dict(self) -> None:
        try:
            self.read_dict()
        except (KeyError, FileNotFoundError):
            self.write_dict()

    def read_dict(self) -> None:
        with shelve.open(os.path.join("shelve", "journal")) as jour:
            self.word_count_map = jour["freq"]
            self.entries_map = jour["entries"]

    def write_dict(self) -> None:
        self.create_word_frequency()
        self.update_entries_from_db()
        pathlib.Path(os.path.join("shelve")).mkdir(parents=True, exist_ok=True)
        with shelve.open(os.path.join("shelve", "journal")) as jour:
            jour["freq"] = self.word_count_map
            jour["entries"] = self.entries_map

    def create_word_frequency(self) -> None:
        content = "".join(self.entries_map.values()).lower()
        self.word_count_map = Counter(re.findall(r"\w+", content))

    def check_for_new_files(self):
        curr_entries = len(self.entries_map)
        all_entries = len(self.get_entries_from_db())
        if all_entries > curr_entries:
            self.console.print(f"{all_entries - curr_entries} new entries found, you can type '-update'")

    def update_entries_from_db(self) -> None:
        self.entries_map = {}
        entries = self.get_entries_from_db()
        for text_raw, ticks in track(entries, description="Updating entries map"):
            text = hp.decode_entities(text_raw).replace("<p>", "").replace("</p>", "\n")
            date = hp.get_date_from_tick(int(ticks))
            self.entries_map[date] = text

    @staticmethod
    def get_entries_from_db() -> List[str]:
        database_path = config["diary.db path"]
        con = sqlite3.connect(database_path)
        entries = con.cursor().execute("SELECT Text, DiaryEntryId FROM Entries").fetchall()
        con.close()
        return entries

    def get_years(self) -> Set[int]:
        return {int(date.split("-")[-1]) for date in self.entries_map.keys()}

    def create_tree_folder_structure(self) -> None:
        self.create_year_and_month_folders()
        self.create_day_files()

    def create_year_and_month_folders(self) -> None:
        for year in [str(y) for y in self.get_years()]:
            if os.path.exists(os.path.join("entries", year)):
                shutil.rmtree(os.path.join("entries", year))
            for month in [str(m) for m in range(1, 12 + 1)]:
                pathlib.Path(os.path.join("entries", year, month)).mkdir(parents=True, exist_ok=True)

    def create_day_files(self) -> None:
        for date, text in self.entries_map.items():
            day, month, year = date.split("-")
            day = day.lstrip("0")
            month = month.lstrip("0")
            with open(os.path.join("entries", year, month, day) + ".txt", "w", encoding="utf-8") as day_file:
                day_file.write(text)

    def get_most_frequent_words(self, count: int) -> list:
        return sorted(self.word_count_map.items(), key=lambda item: item[1], reverse=True)[:count]

    def get_unique_word_count(self) -> int:
        return len(self.word_count_map)

    def get_total_word_count(self) -> int:
        return sum(self.word_count_map.values())

    def get_word_occurrences(self, word: str) -> int:
        return self.word_count_map[word] if word in self.word_count_map else 0

    def get_english_word_count(self) -> int:
        # not accurate cuz a word can be both Slovak and English and I don't have a database of Slovak words to compare
        english_words = set()
        with open(os.path.join("..", "text", "words_alpha.txt")) as f:
            for line in f:
                english_words.add(line.strip())
        return sum(count for word, count in self.word_count_map.items() if word in english_words)

    def get_entry_from_date(self, date: str) -> str:
        # date should be in the format DD.MM.YYYY
        try:
            return self.entries_map[date]
        except KeyError:
            return None

    def get_random_day(self) -> str:
        date, text = random.choice(list(self.entries_map.items()))
        return date + "\n" + text

    def get_longest_day(self) -> str:
        words_in_file = {}  # file: word_count
        for date, text in self.entries_map.items():
            words_in_file[date] = len(text.split())
        date, word_count = sorted(words_in_file.items(), key=lambda item: item[1])[-1]
        return f"{date}\nWord count: {word_count}\n\n{self.entries_map[date]}"

    def find_word(self, word: str, exact_match):
        start = time.time()
        output, occurrences = Finder().find_and_get_output(word, exact_match)
        took_time = round(time.time() - start, 2)
        self.console.print(output)
        self.console.print(f"The word {word} was found {occurrences} times",
                           highlight=False)
        self.console.print(f"Searched through {self.get_total_word_count()} words in {took_time}s",
                           highlight=False)

    @staticmethod
    def create_help_table() -> Table:
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
        table.add_row("-update", "updates journal files and dictionary")
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
                self.find_word(word=val, exact_match=False)
            elif action == "-fp":
                self.find_word(word=val, exact_match=True)
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
                file_content = self.get_entry_from_date(date=val)
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
                self.console.print(
                    f"Percentage of english words: {round(eng_word_count * 100 / self.get_total_word_count(), 3)}%")
            elif action == "-fol":
                self.create_tree_folder_structure()
            elif action == "-h":
                self.console.print(table)
            elif action == "-update":
                entries_before = self.entries_map
                self.update_entries_from_db()
                entries_after = self.entries_map
                if entries_after != entries_before:
                    self.console.print(f"Added {len(entries_after) - len(entries_before)} entries")
                    self.console.print("Proceeding to update dictionary")
                    word_count_before = self.get_total_word_count()
                    self.write_dict()
                    word_count_after = self.get_total_word_count()
                    if word_count_after - word_count_before == 0:
                        self.console.print("No new words found")
                    else:
                        self.console.print(f"Added {word_count_after - word_count_before} words to the dictionary")
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
    Journal().start()
