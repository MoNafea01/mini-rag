import re
import os
import random
import string

def get_clean_file_name(filename: str) -> str:
    # Remove any unwanted characters from the filename
    cleaned_file_name = re.sub(r'[^\w.]', '', filename.strip())
    cleaned_file_name = cleaned_file_name.replace(" ", "_")
    return cleaned_file_name


def generate_random_string(length: int = 12) -> str:
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))


def generate_unique_filename(original_filename: str, project_path: str) -> str:
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
            "filename": f"{random_str}_{original_filename}",
            "path": file_path
        }
