import re
from io import StringIO
from threading import Thread

class Finder:
    
    occurences: int = 0
    exact_match: bool = False
    files_output: dict[int, StringIO] = {}
    
    def __init__(self, files: list[str]):
        self.files = files
        
    def find(self, word: str, exact_match: bool):
        self.exact_match = exact_match
        self.files_output = {}
        self.occurences = 0
        threads = [
            Thread(target=self._find_word_in_file, args=(file, word.lower(), ix))
            for ix, file in enumerate(self.files)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def _find_word_in_file(self, file: str, word: str, ix: int):
        with open(file, encoding="utf-8") as f:
            file_content = f.read()
        date_inserted = False
        sentences = self._split_text_into_sentences(file_content)
        for sentence in sentences:
            if not self.is_word_in_sentence(sentence, word):
                continue
            if ix not in self.files_output:
                self.files_output[ix] = StringIO()
            if not date_inserted:
                self._insert_date(file, ix)
                date_inserted = True
            self._find_word_in_sentence(sentence, word, ix)
        if date_inserted:
            self.files_output[ix].write("\n")

    def _split_text_into_sentences(self, text: str):
        split_regex = "(?<=[.!?\n])\s+"
        return [sentence.strip() for sentence in re.split(split_regex, text)]

    def _find_word_in_sentence(self, sentence: str, word: str, ix: int):
        highlight_style = "bold red"
        for curr_word in sentence.split():
            if self.is_the_same_word(curr_word, word):
                self.occurences += 1
                self.files_output[ix].write(f"[{highlight_style}]{curr_word}[/{highlight_style}] ")
            else:
                self.files_output[ix].write(f"{curr_word} ")
        self.files_output[ix].write("\n")

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

    def _insert_date(self, file_name: str, ix: int):
        file_date_begin = file_name.index("2")
        file_date_end = file_name.index(".txt")
        year, month, day = file_name[file_date_begin : file_date_end].split("-")
        date_style = "blue"
        self.files_output[ix].write(f"[{date_style}]Date: {day}.{month}.{year}[/{date_style}]\n")

    def get_current_output(self):
        return StringIO(
            "".join(i.getvalue() for i in self.files_output.values())
        ).getvalue()
