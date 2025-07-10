from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
import json


def summarise_invocation(result) -> None:
    # -- 2. Set up Rich console and formatting maps --
    console = Console()
    res_map = {
        'passed': {'color': 'green', 'emoji': '✅'},
        'altered': {'color': 'yellow', 'emoji': '⚠️'},
        'rejected': {'color': 'red', 'emoji': '❌'},
    }


    # -- 3. Build the Rich renderable components --

    # A Table for Invocation Results
    inv_table = Table(show_header=True, header_style="bold white", title="Invocation Results")
    inv_table.add_column("Component", style="dim")
    inv_table.add_column("Outcome", justify="center")

    for part, outcome_str in result.invocation_results.items():
        style = res_map.get(outcome_str, {}).get('color', 'white')
        emoji = res_map.get(outcome_str, {}).get('emoji', '➡️')
        outcome_text = Text(f"{emoji} {outcome_str.upper()}", style=style)
        inv_table.add_row(part.replace("_", " ").capitalize(), outcome_text)

    # A Table for Policy Results
    pol_table = Table(show_header=True, header_style="bold white", title="\nPolicy Results")
    pol_table.add_column("Policy", style="dim", width=30)
    pol_table.add_column("Details", width=70)

    for policy, outcome in result.policy_results.items():
        # Assuming the outcome is a dict, format it nicely with Syntax
        outcome_str = json.dumps(outcome, indent=2)
        outcome_syntax = Syntax(outcome_str, "json", theme="solarized-dark", word_wrap=True)
        pol_table.add_row(policy, outcome_syntax)

    # Syntax Panels for Processed Input and Output
    input_color = res_map.get(result.invocation_results['input'], {}).get('color', 'white')
    output_color = res_map.get(result.invocation_results.get('output'), {}).get('color', 'white')
    
    input_panel = Panel(
        Syntax(result.processed_input, "plain", theme="solarized-dark", line_numbers=False, word_wrap=True),
        title="[bold]Processed Input[/bold]",
        border_style=input_color, # The border color reflects the outcome!
        title_align="left",
    )

    output_panel = Panel(
        Syntax((result.processed_output or result.raw_output)[:2000], "plain", theme="solarized-dark", line_numbers=False, word_wrap=True),
        title="[bold]Processed Output[/bold]",
        border_style=output_color, # The border color reflects the outcome!
        title_align="left",
    )


    # -- 4. Group components and print inside a final Panel --
    final_group = Group(
        inv_table,
        pol_table,
        input_panel,
        output_panel,
    )

    console.print(
        Panel(
            final_group,
            title="[bold cyan]Invocation & Policy Summary[/bold cyan]",
            border_style="green"
        )
    )