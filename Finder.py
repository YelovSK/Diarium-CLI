import re
from io import StringIO

class Finder:
    
    occurences: int = 0
    exact_match: bool = False
    find_output: StringIO()
    
    def __init__(self, files: list[str]):
        self.files = files
        
    def find(self, word: str, exact_match: bool):
        self.exact_match = exact_match
        self.find_output = StringIO()
        self.files_output = {}
        self.occurences = 0
        word = word.lower()
        for file in self.files:
            self._find_word_in_file(file, word)

    def _find_word_in_file(self, file: str, word: str):
        with open(file, encoding="utf-8") as f:
            file_content = f.read()
        date_inserted = False
        sentences = self._split_text_into_sentences(file_content)
        for sentence in sentences:
            if not self.is_word_in_sentence(sentence, word):
                continue
            if not date_inserted:
                self._insert_date(file)
                date_inserted = True
            self._find_word_in_sentence(sentence, word)
        if date_inserted:
            self.find_output.write("\n")

    def _split_text_into_sentences(self, text: str):
        split_regex = "(?<=[.!?\n])\s+"
        return [sentence.strip() for sentence in re.split(split_regex, text)]

    def _find_word_in_sentence(self, sentence: str, word: str):
        highlight_style = "bold red"
        for curr_word in sentence.split():
            if self.is_the_same_word(curr_word, word):
                self.occurences += 1
                self.find_output.write(f"[{highlight_style}]{curr_word}[/{highlight_style}] ")
            else:
                self.find_output.write(f"{curr_word} ")
        self.find_output.write("\n")

    def is_word_in_sentence(self, sentence: str, word: str):
        return any(
            self.is_the_same_word(curr_word, word)
            for curr_word in sentence.split()
        )

    def is_the_same_word(self, word1: str, word2: str):
        if self.exact_match:
            return word1.lower() == word2.lower()
        if len(word2) > len(word1): # word1 longer or same
            word1, word2 = word2, word1
        if len(word1) - len(word2) >= len(word2):
            return False
        word1 = word1.lower()
        word2 = word2.lower()
        return word2 in word1

    def _insert_date(self, file_name: str):
        file_date_begin = file_name.index("2")
        file_date_end = file_name.index(".txt")
        year, month, day = file_name[file_date_begin : file_date_end].split("-")
        date_style = "blue"
        self.find_output.write(f"[{date_style}]Date: {day}.{month}.{year}[/{date_style}]\n")

    def get_current_output(self):
        return self.find_output.getvalue()
