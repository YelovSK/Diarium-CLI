from __future__ import annotations
import os
import rich
import click
from click_shell import shell
from diarium_cli.journal import Journal

journal = Journal()
console = rich.console.Console()


@shell(prompt="Diarium-CLI >> ")
def cli():
    console.print("Type 'help' to show commands")


@cli.command()
@click.option("-w", "--word", required=True, help="Word to search for.")
@click.option("-e", "--exact", is_flag=True, help="Search for exact matches.")
def find(word: str, exact: bool = False):
    """Searches for a <word>."""
    journal.find_word(word=word, exact_match=exact)


@cli.command()
@click.option("-w", "--words", default=10, help="Number of top words showed.")
def stats(words: int):
    """Shows stats."""
    console.print("Entries:", len(journal.entries_map))
    console.print("Words:", journal.get_total_word_count())
    console.print("Unique words:", journal.get_unique_word_count())
    console.print(journal.get_most_frequent_words(words))


@cli.command()
@click.option("-w", "--word", required=True, help="Word to search for.")
def count(word: str):
    """Shows the number of occurrences of a <word>."""
    journal.get_word_count(word)


@cli.command()
@click.option("-d", "--date", required=True, help="Format: dd.mm.yyyy")
def day(date: str):
    """Shows a specific entry."""
    file_content = journal.get_entry_from_date(date=date)
    if file_content is None:
        console.print("File not found")
    else:
        console.print(file_content)


@cli.command()
def random():
    """Shows a random entry."""
    console.print(journal.get_random_day())


@cli.command()
def longest():
    """Shows the longest entry."""
    console.print(journal.get_longest_day())


@cli.command()
@click.option("-l", "--list", is_flag=True, help="List words.")
def lang(list: bool = False):
    """Shows the number of English and Slovak words."""
    if list:
        eng_words, sk_words = journal.get_language_words()
        console.print("ENGLISH WORDS:")
        console.print(", ".join(eng_words), style="red")
        console.print("SLOVAK WORDS:")
        console.print(", ".join(sk_words), style="blue")
    eng_count, sk_count = journal.get_language_words_count()
    console.print(
        f"All words: {journal.get_total_word_count()} | English words: {eng_count} | Slovak words: {sk_count}"
    )


@cli.command()
def folder():
    """Puts entries into files into appropriate folders."""
    path = input(f"Directory: (empty for {os.getcwd()}): ")
    if path == "":
        path = os.getcwd() + "/entries"
    elif not os.path.exists(path):
        console.print("Path does not exist")
        return
    new_path = os.path.join(path, "entries")
    journal.create_tree_folder_structure(new_path)


@cli.command()
def clear():
    """Clears console."""
    os.system("cls||clear")


if __name__ == "__main__":
    cli()
