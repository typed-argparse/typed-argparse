import argparse
from typing import Optional


class DefaultHelpFormatter(argparse.HelpFormatter):
    class Unformatted(str):
        pass

    def _get_help_string(self, action: argparse.Action) -> Optional[str]:
        if (
            not isinstance(action.help, DefaultHelpFormatter.Unformatted)
            and action.help is not None
            and action.default is not None
            and action.default is not argparse.SUPPRESS
        ):
            try:
                from yachalk import chalk  # pyright: ignore

                return f"{action.help} {chalk.gray(f'[default: {action.default}]')}"
            except ImportError:
                return f"{action.help} [default: {action.default}]"
        else:
            return action.help
