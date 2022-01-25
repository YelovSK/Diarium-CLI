import re
import os
import datetime
from html.entities import name2codepoint
from typing import List


def get_date_from_filename(filename: str) -> str:
    filename = filename.split("/")[-1]
    file_date_begin = filename.index("2")
    file_date_end = filename.index(".txt")
    year, month, day = filename[file_date_begin: file_date_end].split("-")
    date_style = "blue"
    return f"[{date_style}]Date: {day}.{month}.{year}[/{date_style}]"

def split_text_into_sentences(text: str) -> List[str]:
    split_regex = r"(?<=[.!?\n])\s+"
    return [sentence.strip() for sentence in re.split(split_regex, text)]

def decode_entities(text: str) -> str:
    def unescape(match):
        code = match.group(1)
        if code:
            return chr(int(code, 10))
        code = match.group(2)
        if code:
            return chr(int(code, 16))
        code = match.group(3)
        if code in name2codepoint:
            return chr(name2codepoint[code])
        return match.group(0)
    entity_pattern = re.compile(r'&(?:#(\d+)|(?:#x([\da-fA-F]+))|([a-zA-Z]+));')
    return entity_pattern.sub(unescape, text)

def get_date_from_tick(ticks: int) -> str:
    date = datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=ticks // 10)
    return date.strftime(r"%Y-%m-%d")

def get_file_list(full_path=False) -> List[str]:
    path = os.path.join(os.getcwd(), "Diarium")
    if full_path:
        return [os.path.join(path, file) for file in os.listdir(path)]
    else:
        return os.listdir(path)
