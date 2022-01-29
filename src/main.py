import os
import pathlib
import random
import re
import shutil
import sys
import time
import sqlite3
import json
import helper as hp
from io import StringIO
from collections import Counter
from typing import List
from rich.console import Console
from rich.table import Table
from finder import Finder


class Journal:

    def __init__(self) -> None:
        with open("config.json") as cfg:
            self.config = json.load(cfg)
        self.console = Console()
        self.word_count_map = {}
        self.entries_map = {}
        self.load_entries()
    
    def load_entries(self) -> None:
        start = time.time()
        self.update_entries_from_db()
        self.create_word_frequency()
        took_time = round((time.time() - start) * 1000)
        self.console.print(f"Loaded {len(self.entries_map)} entries and {self.get_total_word_count()} words in {took_time}ms")

    def create_word_frequency(self) -> None:
        content = "".join(self.entries_map.values()).lower()
        self.word_count_map = Counter(re.findall(r"\w+", content))

    def update_entries_from_db(self) -> None:
        self.entries_map = {}
        entries = self.get_entries_from_db()
        for text_raw, ticks in entries:
            text = hp.decode_entities(text_raw).replace("<p>", "").replace("</p>", "\n")
            date = hp.get_date_from_tick(int(ticks))
            self.entries_map[date] = text

    def get_entries_from_db(self) -> List[str]:
        if not os.path.exists(self.config["diary.db path"]):
            self.prompt_to_find_database_file()
        con = sqlite3.connect(self.config["diary.db path"])
        entries = con.cursor().execute("SELECT Text, DiaryEntryId FROM Entries").fetchall()
        con.close()
        return entries

    def prompt_to_find_database_file(self) -> None:
        self.console.print(f"'diary.db' file in '{self.config['diary.db path']}' not found")
        try:
            searched_file = self.find_database_file()
        except FileNotFoundError:
            os.system("pause")
            sys.exit()
        self.console.print(f"Found file in '{searched_file}'")
        while True:
            ans = input("Do you want to add it to config.json? y/n\n>> ").lower()
            if ans == "n":
                sys.exit()
            if ans == "y":
                with open("config.json", "r+") as f:
                    data = json.load(f)
                    data["diary.db path"] = searched_file
                    f.seek(0)
                    json.dump(data, f)
                    f.truncate()
                self.config["diary.db path"] = searched_file
                self.console.print("Path added to config.json")
                break

    def find_database_file(self) -> str:
        appdata_path = os.getenv("LOCALAPPDATA")
        packages_dirs = os.listdir(os.path.join(appdata_path, "Packages"))
        diarium_dir = ""
        for _dir in packages_dirs:
            if "DailyDiary" in _dir:
                diarium_dir = _dir
                break
        if diarium_dir == "":
            raise FileNotFoundError
        diary_path = os.path.join(appdata_path, "Packages", diarium_dir, "LocalState", "diary.db")
        if not os.path.exists(diary_path):
            raise FileNotFoundError
        return diary_path

    def create_tree_folder_structure(self) -> None:
        if os.path.exists("entries"):
            shutil.rmtree("entries")
        for date, text in self.entries_map.items():
            day, month, year = date.split(".")
            day = day.lstrip("0")
            month = month.lstrip("0")
            if not os.path.exists(os.path.join("entries", year, month)):
                pathlib.Path(os.path.join("entries", year, month)).mkdir(parents=True, exist_ok=True)
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

    def get_entry_from_date(self, date: str) -> str|None:
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
        output = StringIO()
        output.write(date + "\n")
        output.write(self.entries_map[date])
        output.write(f"\nWord count: {word_count}")
        return output.getvalue()

    def find_word(self, word: str, exact_match) -> None:
        start = time.time()
        output, occurrences = Finder(self.entries_map).find_and_get_output(word, exact_match)
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
                self.console.print("Entries:", len(self.entries_map))
                self.console.print("Words:", self.get_total_word_count())
                self.console.print("Unique words:", self.get_unique_word_count())
                if not val or not val.isnumeric():
                    val = 10
                self.console.print(self.get_most_frequent_words(int(val)))
            elif action == "-c":
                self.console.print("Exact matches:", self.get_word_occurrences(val))
                occurrences = Finder(self.entries_map).find_and_get_occurrences(word=val, exact_match=False)
                self.console.print("All matches:", occurrences)
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
                self.console.print(f"All words: {self.get_total_word_count()} | English words: {eng_word_count}")
                self.console.print(
                    f"Percentage of english words: {round(eng_word_count * 100 / self.get_total_word_count(), 3)}%")
            elif action == "-fol":
                self.create_tree_folder_structure()
            elif action == "-h":
                self.console.print(table)
            elif action == "-clr":
                os.system("cls")
            elif action == "-q":
                break
            else:
                self.console.print("Command not recognized. Type '-h' for help.")


if __name__ == "__main__":
    if not os.path.exists("config.json"):
        Console().print("'config.json' not found")
        os.system("pause")
        sys.exit()
    Journal().start()
