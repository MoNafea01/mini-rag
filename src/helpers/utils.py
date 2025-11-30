import re
import os
import random
import string
from typing import Dict


def get_clean_file_name(filename: str) -> str:
    # Remove any unwanted characters from the filename
    cleaned_file_name = re.sub(r'[^\w.]', '_', filename.strip())
    cleaned_file_name = cleaned_file_name.replace(" ", "_")
    return cleaned_file_name


def generate_random_string(length: int = 12) -> str:
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))


def generate_unique_filepath(original_filename: str, project_path: str) -> Dict[str, str]:
    random_str = generate_random_string()
    original_filename = get_clean_file_name(original_filename)
    
    is_new = False
    while not is_new:
        file_path = os.path.join(project_path, f"{random_str}_{original_filename}")
        if not os.path.exists(file_path):
            is_new = True
        else:
            random_str = generate_random_string()
    
    return {
        "filename": f"{original_filename}",
        "path": file_path,
        "prefix": random_str
    }


def message_handler(message: str, 
                    keep_all=False, 
                    *args, 
                    **kwargs) -> dict:
    
    new_kwargs = {}
    for key, val in kwargs.items():
        if keep_all:
            new_kwargs = kwargs
            break
        
        if not is_empty(val):
            new_kwargs[key] = val

    message = dict(message=message, **new_kwargs)
    return message


def is_empty(value):
    """Recursively determine if a value is empty."""
    
    if value in (None, '', [], {}, 0, '0'):
        return True

    if isinstance(value, dict):
        return all(is_empty(v) for v in value.values())

    if isinstance(value, (list, tuple, set)):
        return all(is_empty(v) for v in value)

    return False
