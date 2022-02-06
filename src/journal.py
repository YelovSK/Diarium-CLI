from __future__ import annotations
import os
import pathlib
import random
import re
import shutil
import sys
import time
import sqlite3
import platform
import src.helper as hp
from collections import Counter
from rich.console import Console
from src.finder import Finder


class Journal:

    def __init__(self) -> None:
        self.console = Console()
        self.word_count_map = {}
        self.entries_map = {}
        self.load_entries()

    def load_entries(self) -> None:
        start = time.time()
        self.update_entries_from_db()
        self.create_word_frequency()
        took_time = round((time.time() - start) * 1000)
        self.console.print(
            f"Loaded {len(self.entries_map)} entries and {self.get_total_word_count()} words in {took_time}ms")

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

    def get_entries_from_db(self) -> list[str]:
        try:
            searched_file = self.find_database_file()
        except FileNotFoundError:
            self.console.print("'diary.db' file not found")
            input("Press the <Enter> key to exit...")
            sys.exit()
        con = sqlite3.connect(searched_file)
        entries = con.cursor().execute("SELECT Text, DiaryEntryId FROM Entries").fetchall()
        con.close()
        return entries

    @staticmethod
    def find_database_file() -> str:
        if platform.system() != "Windows":
            raise FileNotFoundError
        appdata_path = os.getenv("LOCALAPPDATA")
        packages_dirs = os.listdir(os.path.join(appdata_path, "Packages"))
        for _dir in packages_dirs:
            if "DailyDiary" in _dir:
                diary_path = os.path.join(appdata_path, "Packages", _dir, "LocalState", "diary.db")
                if os.path.exists(diary_path):
                    return diary_path
                break
        raise FileNotFoundError

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

    def get_entry_from_date(self, date: str) -> str | None:
        try:
            return self.entries_map[date]
        except KeyError:
            return None

    def get_random_day(self) -> str:
        date, text = random.choice(list(self.entries_map.items()))
        return date + "\n" + text

    def get_longest_day(self) -> str:
        date, text = sorted(self.entries_map.items(), key=lambda x: len(x[1].split()))[-1]
        return date + "\n" + text + "\n" + f"Word count: {len(text.split())}"

    def find_word(self, word: str, exact_match) -> None:
        start = time.time()
        output, occurrences = Finder(self.entries_map).find_and_get_output(word, exact_match)
        took_time = round(time.time() - start, 2)
        self.console.print(output)
        self.console.print(f"The word {word} was found {occurrences} times",
                           highlight=False)
        self.console.print(f"Searched through {self.get_total_word_count()} words in {took_time}s",
                           highlight=False)

    def get_word_count(self, word: str) -> None:
        self.console.print("Exact matches:", self.get_word_occurrences(word))
        occurrences = Finder(self.entries_map).find_and_get_occurrences(word=word, exact_match=False)
        self.console.print("All matches:", occurrences)
