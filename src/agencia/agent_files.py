import os
from agents import function_tool
from pydantic import BaseModel


class FinalPost(BaseModel):
    body: str


@function_tool
def file_generator(directory: str):
    """
    Generator that yields the next file from the given directory.

    :param directory: Path to the directory to iterate over files.
    """
    if not os.path.isdir(directory):
        raise ValueError(f'{directory} is not a valid directory')

    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            yield file_path


@function_tool
def print_file_md(file: str) -> str:
    print(file)
    return file + 'end;'


@function_tool
def get_post_md(mask:str) -> str:
    s= 'ab ' + str(mask) + ' cd'
    print(s)
    return s
    # body=file_generator(directory)
