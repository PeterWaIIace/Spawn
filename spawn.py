from pydantic_ai import Agent
from dotenv import load_dotenv
from datetime import datetime
import argparse
import re
import os

name_pattern = r"NAME:\s*(.*?\.py)"
name_pattern_no_py = r"NAME:([^\s]+)"

load_dotenv()

coder = Agent(  
    'google-gla:gemini-1.5-flash',
    system_prompt='Generate python program based on the prompt. Top line should be program name, preceeded by `NAME:`. Do not generate any other text. If you are unable to generate python program, generate ```program=NONE```.',  
)

requirements_checker = Agent(  
    'google-gla:gemini-1.5-flash',
    system_prompt='You check the program file and generate requirements.txt for it. Do not generate any other text. If you are unable to generate python program, generate NONE response.',  
)


def extract_program(text):
    # Split text into lines
    lines = text.splitlines()
    n = 0
    for n, line in enumerate(lines):
        if '```' in line:
            break

    # Remove first 2 (NAME, and ```python) and last 1 line (```)
    trimmed_lines = lines[n:-1]

    # Join back into a single string
    program = "\n".join(trimmed_lines)
    program = program.replace("```python", "").replace("```", "").strip()
    return program

def find_program_name(text):
    matches = re.findall(name_pattern, text)
    if len(matches) <= 0:
        matches = re.findall(name_pattern_no_py, text)
        if len(matches) <= 0:
            matches[0] = matches[0] + '.py'
        else:
            print(f"Error occurred. No name found in: {text}")
            return None

    program_name = matches[0]
    return program_name

def make_dirs_recursive(path):
    if not os.path.exists(path):
        parent = os.path.dirname(path)
        if parent and not os.path.exists(parent):
            make_dirs_recursive(parent)
        os.mkdir(path)

def main():
    parser = argparse.ArgumentParser(description="Spawn AI script")
    parser.add_argument("program", help="Description of the program")
    parser.add_argument("-o","--output", help="output file path", default=".")
    args = parser.parse_args()

    make_dirs_recursive(args.output)

    result = coder.run_sync(f'This is program description: {args.program}')
    program = extract_program(result.output)

    program_name = find_program_name(result.output)
    if program_name is None:
        return None

    copyright_notice = f"# Copyright {datetime.now().year} <Insert your copyrights> \n# This code was generated with spawn: https://github.com/PeterWaIIace/Spawn"
    program = copyright_notice + "\n" + program
    with open(f"{args.output}/"+program_name,'w+') as f:
        f.write(program)

    result = requirements_checker.run_sync(f'This is program: {program}')

    requirements_txt = extract_program(result.output)
    with open(f"{args.output}/requirements.txt",'w+') as f:
        f.write(requirements_txt)


if __name__ == "__main__":
    main()