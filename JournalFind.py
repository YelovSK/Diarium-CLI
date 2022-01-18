import os
import pathlib
import random
import re
import shelve
import shutil
import time
from collections import Counter
from rich.console import Console
from rich.table import Table
from Finder import Finder


class Journal:

    def __init__(self, base_folder: str = os.getcwd()):
        self.base = base_folder
        self.path = os.path.join(self.base, "Diarium")
        self.files = list(os.listdir(self.path))
        self.years = self.get_years()
        self.console = Console()
        self.word_count_dict = {}
        self.files_list_path = os.path.join(self.base, "files.txt")
        self.check_file_count_mismatch()
        files_full_path = [os.path.join(self.path, file) for file in self.files]
        self.finder = Finder(files_full_path)

    def check_file_count_mismatch(self) -> None:
        if not os.path.exists(self.files_list_path):
            with open(self.files_list_path, "w") as f:
                f.write("-1")
        with open(self.files_list_path) as f:
            files_num = int(f.read())
        # files_num -> last checked number of files
        # len(self.files) -> number of files in the Diarium folder
        if files_num != len(self.files):
            self.console.print("File count mismatch, formatting...")
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
        with shelve.open(os.path.join(self.base, "shelve", "journal")) as jour:
            self.word_count_dict = jour["freq"]

    def write_dict(self) -> None:
        self.create_word_frequency()
        pathlib.Path(os.path.join(self.base, "shelve")).mkdir(parents=True, exist_ok=True)
        with shelve.open(os.path.join(self.base, "shelve", "journal")) as jour:
            jour["freq"] = self.word_count_dict

    def create_word_frequency(self) -> None:
        file_content_list = []
        for file in self.files:
            with open(os.path.join(self.path, file), encoding="utf-8") as f:
                file_content_list.append(f.read())
        content = "".join(file_content_list).lower()
        self.word_count_dict = Counter(re.findall(r"\w+", content))

    def get_years(self) -> set[int]:
        YEAR_START_IX = 8
        YEAR_END_IX = YEAR_START_IX + 4
        return {int(file[YEAR_START_IX: YEAR_END_IX]) for file in self.files}

    def create_tree_folder_structure(self) -> None:
        self.create_year_and_month_folders()
        self.create_day_files()
        self.update_file_count()

    def create_year_and_month_folders(self) -> None:
        for year in [str(y) for y in self.years]:
            if os.path.exists(os.path.join(self.base, year)):
                shutil.rmtree(os.path.join(self.base, year))
            for month in [str(m) for m in range(1, 12 + 1)]:
                pathlib.Path(os.path.join(year, month)).mkdir(parents=True, exist_ok=True)

    def create_day_files(self) -> None:
        for file in self.files:
            with open(os.path.join(self.path, file), errors="ignore") as f:
                file_content = f.read()
            year, month, day = file[file.index("2"):].split("-")
            if month[0] == "0":
                month = month[1:]
            if day[0] == "0":
                day = day[1:]
            with open(os.path.join(year, month, day), "w") as day_file:
                day_file.write(file_content)

    def update_file_count(self) -> None:
        with open(self.files_list_path, "w") as f:
            f.write(str(len(self.files)))

    def get_most_frequent_words(self, count: int) -> list:
        return sorted(self.word_count_dict.items(), key=lambda item: item[1], reverse=True)[:count]

    def get_unique_word_count(self) -> int:
        return len(self.word_count_dict)

    def get_total_word_count(self) -> int:
        return sum(self.word_count_dict.values())

    def get_word_occurrences(self, word: str) -> int:
        if word in self.word_count_dict:
            return self.word_count_dict[word]
        return 0

    def percentage_english_words(self) -> None:
        # bad statistic cuz a word can be in both Slovak and English and I don't have a database of Slovak words to compare
        english_words = set()
        with open(os.path.join("..", "text", "words_alpha.txt")) as f:
            for line in f:
                english_words.add(line.strip())
        all_words_count = self.get_total_word_count()
        english_word_count = sum(count for word, count in self.word_count_dict.items() if word in english_words)
        self.console.print(f"All words: {all_words_count} | English word count: {english_word_count}")
        self.console.print(f"Percentage of english words: {round(english_word_count * 100 / all_words_count, 3)}%")

    def get_random_day(self) -> str:
        with open(os.path.join(self.path, random.choice(self.files)), encoding="utf-8") as f:
            return f.read()

    def create_help_table(self) -> Table:
        table = Table(title="Functions")
        for col in ("Input", "Action", "Arguments"):
            table.add_column(col)
        table.add_row("-h", "help", "")
        table.add_row("-f", "find", "text")
        table.add_row("-fp", "find exact match", "text")
        table.add_row("-s", "stats", "number of top words showed")
        table.add_row("-c", "count occurrences of text", "text")
        table.add_row("-r", "random entry", "")
        table.add_row("-lang", "eng/sk percentage", "")
        table.add_row("-fol", "create folder structure", "")
        table.add_row("-fix", "refresh dictionary", "")
        table.add_row("-clr", "clear console", "")
        table.add_row("-q", "quit", "")
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
            elif action == "-r":
                self.console.print(self.get_random_day())
            elif action == "-lang":
                self.percentage_english_words()
            elif action == "-fol":
                self.create_tree_folder_structure()
            elif action == "-h":
                self.console.print(table)
            elif action == "-fix":
                self.write_dict()
                self.update_file_count()
                self.console.print("Done fixing")
            elif action == "-clr":
                os.system("cls")
            elif action == "-q":
                break
            else:
                self.console.print("Command not recognized. Type '-h-' for help.")


Journal().start()
