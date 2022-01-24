import helper as hp
from io import StringIO
from rich.progress import track

class Finder:

    def __init__(self, files: list[str]):
        self.files = files
        self.occurrences = 0
        self.exact_match = False

    def find_and_get_output(self, word: str, exact_match: bool) -> str:
        return self._find(word, exact_match)

    def find_and_get_occurrences(self, word: str, exact_match: bool) -> int:
        self._find(word, exact_match)
        return self.occurrences

    def get_current_occurrences(self) -> int:
        return self.occurrences

    def _find(self, word: str, exact_match: bool) -> str:
        self.exact_match = exact_match
        self.occurrences = 0
        word = word.lower()
        return "".join(
            self._find_word_in_file(file, word)
            for file in track(self.files, description="Searching")
        )

    def _find_word_in_file(self, file: str, word: str) -> str:
        file_output = StringIO()
        with open(file, encoding="utf-8") as f:
            file_content = f.read()
        sentences = hp.split_text_into_sentences(file_content)
        sentences_containing_word = [s for s in sentences if self._is_word_in_sentence(s, word)]
        if not sentences_containing_word:
            return file_output.getvalue()
        file_output.write(hp.get_date_from_filename(file) + "\n")
        for sentence in sentences_containing_word:
            file_output.write(self._find_word_in_sentence(sentence, word) + "\n")
        file_output.write("\n")
        return file_output.getvalue()

    def _find_word_in_sentence(self, sentence: str, word: str) -> str:
        sentence_output = StringIO()
        highlight_style = "bold red"
        for curr_word in sentence.split():
            if self._is_the_same_word(curr_word, word):
                self.occurrences += 1
                sentence_output.write(f"[{highlight_style}]{curr_word}[/{highlight_style}] ")
            else:
                sentence_output.write(f"{curr_word} ")
        return sentence_output.getvalue()

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
