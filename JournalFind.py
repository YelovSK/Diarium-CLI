import re, shelve, random, os, shutil, pathlib
from rich.console import Console
from rich.table import Table
from collections import Counter

class Journal:

    def __init__(self, base_folder=os.getcwd()):
        self.base = base_folder
        self.path = self.base + "\\Diarium"
        self.files = [f for f in os.listdir(self.path)]
        self.years = self.get_years()
        self.console = Console()
        if (not os.path.exists(self.base+'\\files.txt')):
            with open(self.base+'\\files.txt', "w") as f:
                f.write("-1")
        with open(self.base+'\\files.txt') as f:
            files_num = int(f.read())
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
            pathlib.Path(f"{self.base}\\shelve").mkdir(parents=True, exist_ok=True)
            self.write_dict()

    def read_dict(self):
        with shelve.open(f'{self.base}\\shelve\\journal') as jour:
            self.words = jour['words']
            self.freq_table = jour['freq']

    def write_dict(self):
        self.words = {}
        self.freq_table = self.freq()
        with shelve.open(f'{self.base}\\shelve\\journal') as jour:
            jour['words'] = self.words
            jour['freq'] = self.freq()

    def update_file_count(self):
        with open(self.base+'\\files.txt', "w") as f:
            f.write(str(len(self.files)))

    def get_years(self):
        return {int(file[8:12]) for file in self.files}

    def create_tree_folder_structure(self):
        file_count = 0
        for year in self.years:
            if os.path.exists(f"{self.base}\\{year}"):
                shutil.rmtree(f"{self.base}\\{year}")
            for i in range(1, 13):
                pathlib.Path(f'{year}/{i}').mkdir(parents=True, exist_ok=True)
        for file in self.files:
            with open(f'{self.path}\\{file}', 'r', errors='ignore') as f:
                content = f.read()
                txt = file[8:].split('-')
                txt[2] = txt[2][:txt[2].find('.')]
                if txt[2][0] == '0':
                    txt[2] = txt[2][1:]
                if txt[1][0] == '0':
                    txt[1] = txt[1][1:]
                with open(f'{txt[0]}/{txt[1]}/{txt[2]}.txt', 'w') as new:
                    new.write(content)
                    file_count += 1
        with open(self.base+'\\files.txt', 'w') as f:
            f.write(str(len(self.files)))
        return file_count

    def freq(self):
        file_content_list = []
        for file in self.files:
            with open(f'{self.path}\\{file}', 'r', encoding='utf-8') as f:
                file_content_list.append(f.read())
        content = "".join(file_content_list)
        self.words = Counter(re.findall("\w+", content.lower()))
        return sorted(self.words.items(), key=lambda x: x[1], reverse=True)

    def frequency_table(self, count=20):
        return self.freq_table[:count]

    def unique_word_count(self):
        return len(self.freq_table)

    def total_word_count(self):
        return sum(self.words.values())

    def find_word(self, word):
        count = 0
        highlight_style = "bold red"
        output_list = []
        for file in self.files:
            with open(f'{self.path}\\{file}', 'r', encoding='utf-8') as f:
                txt = f.read()
                putDate, foundWord = False, False
                for sentence in re.split('(?<=[.!?\n])\s+', txt):
                    sentence = sentence.strip()
                    if re.search(word, sentence, re.IGNORECASE):
                        if not putDate:
                            y, m, d = file[8:-4].split('-')
                            output_list.append(f'[blue]Date: {d}.{m}.{y}[/blue]\n')
                        putDate, foundWord = True, True
                        for w in sentence.split():
                            if word.lower() in w.lower():
                                count += 1
                                output_list.append(f'[{highlight_style}]{w}[/{highlight_style}]')
                            else:
                                output_list.append(f"{w}")
                        output_list[-1] += "\n"
            if foundWord:
                output_list.append("\n")

        return " ".join(output_list), count

    def random_entry(self):
        with open(self.path+"\\"+random.choice(self.files), 'r', encoding='utf-8') as f:
            return f.read()

    def start(self):
        print("Type '-h' for help")
        table = Table(title="Functions")
        for col in ("Input", "Action", "Arguments"):
            table.add_column(col)
        table.add_row("-h", "help", "")
        table.add_row("-f", "find", "text")
        table.add_row("-s", "stats", "number of top words showed")
        table.add_row("-c", "count occurences of text", "text")
        table.add_row("-r", "random entry", "")
        table.add_row("-fix", "re-calculate shit", "")
        table.add_row("-clr", "clear console", "")
        table.add_row("-q", "quit", "")
        while True:
            user_input = input(">> ")
            if len(user_input.split()) <= 1:
                action, val = user_input, ""
            else:
                action, val = user_input.split()[0], " ".join(user_input.split()[1:])
            if action == "-f":
                out, count = self.find_word(val)
                self.console.print(f"{out}The word {val} was found {count} times", highlight=False)
            elif action == "-s":
                self.console.print("All words count:", self.total_word_count())
                self.console.print("Unique words count:", self.unique_word_count())
                if not val or not val.isnumeric():
                    val = 10
                self.console.print(self.frequency_table(int(int(val))))
            elif action == "-c":
                print(f"The word '{val}' was found {self.words[val]} times")
            elif action == "-r":
                print(self.random_entry())
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


jour = Journal()
jour.start()