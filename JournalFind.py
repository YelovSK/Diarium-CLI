import re, shelve, random, os, shutil, pathlib
from rich.console import Console
from rich.table import Table
from collections import Counter

class Journal:

    def __init__(self, base_folder=os.getcwd()):
        self.base = base_folder
        self.path = os.path.join(self.base, "Diarium")
        self.files = list(os.listdir(self.path))
        self.years = self.get_years()
        self.console = Console()
        self.word_count_list = []
        self.word_count_dict = {}
        self.files_list_path = os.path.join(self.base, "files.txt")
        if not os.path.exists(self.files_list_path):
            open(self.files_list_path, "w").write("-1")
        self.check_file_count_mismatch()

    def check_file_count_mismatch(self):
        files_num = int(open(self.files_list_path).read())
        # files_num -> last checked number of files
        # len(self.files) -> number of files in the Diarium folder
        if files_num != len(self.files):
            self.console.print("File count mismatch, formatting...")
            self.write_dict()
            self.update_file_count()
        else:
            self.init_dict()

    def init_dict(self):
        try:
            self.read_dict()
        except KeyError:
            self.write_dict()
        except FileNotFoundError:
            pathlib.Path(os.path.join(self.base, "shelve")).mkdir(parents=True, exist_ok=True)
            self.write_dict()

    def read_dict(self):
        with shelve.open(os.path.join(self.base, "shelve", "journal")) as jour:
            self.word_count_list = jour["words"]
            self.word_count_dict = jour["freq"]

    def write_dict(self):
        self.create_word_frequency()
        with shelve.open(os.path.join(self.base, "shelve", "journal")) as jour:
            jour["words"] = self.word_count_list
            jour["freq"] = self.word_count_dict
            
    def create_word_frequency(self):
        file_content_list = []
        for file in self.files:
            with open(os.path.join(self.path, file), encoding="utf-8") as f:
                file_content_list.append(f.read())
        content = "".join(file_content_list).lower()
        self.word_count_dict = Counter(re.findall("\w+", content))
        self.word_count_list = sorted(self.word_count_dict.items(), key=lambda x: x[1], reverse=True)

    def get_years(self):
        return {int(file[8:12]) for file in self.files}
 
    def create_tree_folder_structure(self):
        self.create_year_and_month_folders()
        self.create_day_files()
        self.update_file_count()
        
    def create_year_and_month_folders(self):
        for year in self.years:
            if os.path.exists(os.path.join(self.base, year)):
                shutil.rmtree(os.path.join(self.base, year))
            for month in range(1, 12+1):
                pathlib.Path(os.path.join(year, month)).mkdir(parents=True, exist_ok=True)
                
    def create_day_files(self):
        for file in self.files:
            file_content = open(os.path.join(self.path, file), errors="ignore").read()
            year, month, day = file[8:].split("-")
            if month[0] == "0":
                month = month[1:]
            if day[0] == "0":
                day = day[1:]
            with open(os.path.join(year, month, day+".txt"), "w") as day_file:
                day_file.write(file_content)
                
    def update_file_count(self):
        open(self.files_list_path, "w").write(str(len(self.files)))

    def get_most_frequent_words(self, count=20):
        return self.word_count_list[:count]

    def get_unique_word_count(self):
        return len(self.word_count_dict)

    def get_total_word_count(self):
        return sum(self.word_count_dict.values())

    def percentage_english_words(self):
        # bad statistic cuz a word can be in both Slovak and English and I don't have a databse of Slovak words to compare
        english_words = set()
        with open(os.path.join("..", "text", "words_alpha.txt")) as f:
            for line in f:
                english_words.add(line.strip())
        all_words_count = self.get_total_word_count()
        english_word_count = sum(count for word, count in self.word_count_list if word in english_words)
        self.console.print(f"All words: {all_words_count} | English word count: {english_word_count}")
        self.console.print(f"Percentage of english words: {round(english_word_count*100 / all_words_count, 3)}%")

    def find_word_in_journal(self, word):
        self.occurences = 0
        self.output_list = []
        for file in self.files:
            self.find_word_in_file(file, word)
        return " ".join(self.output_list), self.occurences

    def find_word_in_file(self, file, word):
        file_content = open(os.path.join(self.path, file), encoding="utf-8").read()
        date_inserted = False
        sentences = self.split_text_into_sentences(file_content)
        for sentence in sentences:
            if not re.search(word, sentence, re.IGNORECASE):
                continue
            if not date_inserted:
                self.insert_date(file)
                date_inserted = True
            self.find_word_in_sentence(sentence, word)
        if date_inserted:
            self.output_list.append("\n")

    def split_text_into_sentences(self, text):
        split_regex = "(?<=[.!?\n])\s+"
        return [sentence.strip() for sentence in re.split(split_regex, text)]
            
    def find_word_in_sentence(self, sentence, word):
        highlight_style = "bold red"
        for curr_word in sentence.split():
            if word.lower() in curr_word.lower():
                self.occurences += 1
                self.output_list.append(f"[{highlight_style}]{curr_word}[/{highlight_style}]")
            else:
                self.output_list.append(curr_word)
        self.output_list[-1] += "\n"

    def insert_date(self, file_name):
        file_date_begin = file_name.index("2")
        file_date_end = file_name.index(".txt")
        year, month, day = file_name[file_date_begin : file_date_end].split("-")
        date_style = "blue"
        self.output_list.append(f"[{date_style}]Date: {day}.{month}.{year}[/{date_style}]\n")

    def random_entry(self):
        with open(os.path.join(self.path, random.choice(self.files)), encoding="utf-8") as f:
            return f.read()

    def create_help_table(self):
        table = Table(title="Functions")
        for col in ("Input", "Action", "Arguments"):
            table.add_column(col)
        table.add_row("-h", "help", "")
        table.add_row("-f", "find", "text")
        table.add_row("-s", "stats", "number of top words showed")
        table.add_row("-c", "count occurences of text", "text")
        table.add_row("-r", "random entry", "")
        table.add_row("-lang", "eng/sk percentage", "")
        table.add_row("-fix", "re-calculate shit", "")
        table.add_row("-clr", "clear console", "")
        table.add_row("-q", "quit", "")
        return table

    def start(self):
        self.console.print("Type '-h' for help")
        table = self.create_help_table()
        while True:
            user_input = input(">> ")
            if len(user_input.split()) <= 1:
                action, val = user_input, ""
            else:
                action, val = user_input.split()[0], " ".join(user_input.split()[1:])
            if action == "-f":
                out, count = self.find_word_in_journal(val)
                self.console.print(f"{out}The word {val} was found {count} times", highlight=False)
            elif action == "-s":
                self.console.print("All words count:", self.get_total_word_count())
                self.console.print("Unique words count:", self.get_unique_word_count())
                if not val or not val.isnumeric():
                    val = 10
                self.console.print(self.get_most_frequent_words(int(int(val))))
            elif action == "-c":
                self.console.print(f"The word '{val}' was found {self.word_count_dict[val]} times")
            elif action == "-r":
                self.console.print(self.random_entry())
            elif action == "-lang":
                self.percentage_english_words()
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


Journal().start()
