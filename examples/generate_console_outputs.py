import subprocess
from pathlib import Path
from typing import Dict, List

import yaml

_EXAMPLES_PATH = Path(__file__).parent
_PROJECT_ROOT = _EXAMPLES_PATH.parent
_COMMANDS_FILE = _EXAMPLES_PATH / "commands.yaml"


def main() -> None:
    scripts: Dict[str, List[str]] = yaml.safe_load(_COMMANDS_FILE.read_text())

    for relative_script_path, all_call_args in scripts.items():
        script_path = _EXAMPLES_PATH / relative_script_path

        print(f"\n *** Processing: '{script_path}'\n")

        console_file_contents = []

        for call_args in all_call_args:
            actual_cmd = f"python {script_path.relative_to(_PROJECT_ROOT)} {call_args}"
            pseudo_cmd = f"$ python {script_path.name} {call_args}"
            print(pseudo_cmd)

            output = subprocess.check_output(actual_cmd, cwd=_PROJECT_ROOT, shell=True).decode()
            print(output)

            console_file_contents.append(pseudo_cmd)
            console_file_contents.append(output)

        console_output_path = script_path.with_suffix(".console")
        console_output_path.write_text("\n".join(console_file_contents))


if __name__ == "__main__":
    main()
