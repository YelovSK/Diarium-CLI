import re
from io import StringIO


def split_text_into_sentences(text: str):
    split_regex = r"(?<=[.!?\n])\s+"
    return [sentence.strip() for sentence in re.split(split_regex, text)]


class Finder:

    def __init__(self, files: list[str]):
        self.files = files
        self.occurrences = 0
        self.files_output = {}
        self.find_output = StringIO()
        self.exact_match = False

    def find_and_get_output(self, word: str, exact_match: bool) -> str:
        self._find(word, exact_match)
        return self.find_output.getvalue()

    def find_and_get_occurrences(self, word: str, exact_match: bool) -> int:
        self._find(word, exact_match)
        return self.occurrences

    def get_current_occurrences(self) -> int:
        return self.occurrences

    def _find(self, word: str, exact_match: bool):
        self.exact_match = exact_match
        self.find_output = StringIO()
        self.occurrences = 0
        self.files_output = {}
        word = word.lower()
        for file in self.files:
            self._find_word_in_file(file, word)

    def _find_word_in_file(self, file: str, word: str) -> None:
        with open(file, encoding="utf-8") as f:
            file_content = f.read()
        sentences = split_text_into_sentences(file_content)
        sentences_containing_word = [s for s in sentences if self._is_word_in_sentence(s, word)]
        if not len(sentences_containing_word):
            return
        self._insert_date(file)
        for sentence in sentences_containing_word:
            self._find_word_in_sentence(sentence, word)
        self.find_output.write("\n")

    def _find_word_in_sentence(self, sentence: str, word: str) -> None:
        highlight_style = "bold red"
        for curr_word in sentence.split():
            if self._is_the_same_word(curr_word, word):
                self.occurrences += 1
                self.find_output.write(f"[{highlight_style}]{curr_word}[/{highlight_style}] ")
            else:
                self.find_output.write(f"{curr_word} ")
        self.find_output.write("\n")

    def _is_word_in_sentence(self, sentence: str, word: str) -> bool:
        return any(
            self._is_the_same_word(curr_word, word)
            for curr_word in sentence.split()
        )

    def _is_the_same_word(self, word1: str, word2: str) -> bool:
        if self.exact_match:
            return word1.lower() == word2.lower()
        if len(word2) > len(word1):  # word1 longer or same
            word1, word2 = word2, word1
        if len(word1) - len(word2) >= len(word2):
            return False
        word1 = word1.lower()
        word2 = word2.lower()
        return word2 in word1

    def _insert_date(self, file_name: str) -> None:
        file_date_begin = file_name.index("2")
        file_date_end = file_name.index(".txt")
        year, month, day = file_name[file_date_begin: file_date_end].split("-")
        date_style = "blue"
        self.find_output.write(f"[{date_style}]Date: {day}.{month}.{year}[/{date_style}]\n")
