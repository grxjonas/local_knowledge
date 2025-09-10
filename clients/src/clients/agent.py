import os
from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP
import asyncio
from rich.live import Live
from rich.markdown import CodeBlock, Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.console import Console, ConsoleOptions, RenderResult

from clients.prompts import get_system_prompt, get_instructions
from typing import TypedDict
import datetime
from zoneinfo import ZoneInfo
import logfire
logfire.configure(token="pylf_v1_eu_Ws6XwsLq0GGmwCV1pQtzPZLZbkZg6h04kLmcwsqZWxM0",
service_name="Hypergene Local Knowledge")
logfire.instrument_pydantic_ai()
cli_system_prompt = get_system_prompt()
cli_instructions = get_instructions()
# --- User deps ---
WHOAMI = os.getenv("WHOAMI", "BI-Consultant")
MYROLE = os.getenv("WHOAMI", "BI-Consultant at Hypergene AB")
class User(TypedDict):
    name: str
    role: str
    current_time: str

def create_deps() -> User:
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Madrid"))
    return User(name=WHOAMI, role = MYROLE, current_time=now.isoformat())

user = create_deps()
CUSTOMER = os.getenv("CUSTOMER", "Hypergene")

server = MCPServerStreamableHTTP("http://localhost:8051/mcp")

agent = Agent("gpt-4o-mini", mcp_servers=[server], deps_type=User)

@agent.system_prompt(dynamic = True)
def get_system_prompt(ctx: RunContext[User]) -> str:
    return cli_system_prompt

@agent.system_prompt
def get_user_info(ctx: RunContext[User]):
    return f"Jag är {ctx.deps['name']}"

@agent.tool
def get_current_date_and_time(ctx: RunContext[User]) -> str:
    return f"Nuvarande datum och tid är: {ctx.deps['current_time']}."

@agent.instructions
def get_format_instructions(ctx: RunContext[User]) -> str:
    msgs = getattr(ctx, "messages", None)
    if msgs and len(msgs) > 0:
        return cli_instructions + f" Nuvarande datum och tid är: {ctx.deps['current_time']}."
    else:
        return ""
# --- Optional: prettify code blocks in CLI ---
def prettier_code_blocks():
    """Make rich code blocks prettier and easier to copy."""
    class SimpleCodeBlock(CodeBlock):
        def __rich_console__(self, console: Console, options: ConsoleOptions):
            code = str(self.text).rstrip()
            yield Text(self.lexer_name, style='dim')
            yield Syntax(
                code,
                self.lexer_name,
                theme=self.theme,
                background_color='default',
                word_wrap=True,
            )
            yield Text(f'/{self.lexer_name}', style='dim')

    Markdown.elements['fence'] = SimpleCodeBlock

# --- CLI run function ---
async def run():
    history = []
    prettier_code_blocks()
    console = Console()

    with Live('', console=console, vertical_overflow='visible') as live:
        async with agent.run_stream(
            f"Jag är {user['name']}. Vilken underbar dag! Ge mig ett glad och överdrivet positiv hälsning för att höja stämningen ännu mer!",
            message_history=history,
            deps=user
        ) as result:
            async for message in result.stream():
                live.update(Markdown(message))
            await result.get_output()

    history = result.all_messages()
    print(f"Ställ en fråga om {CUSTOMER} ('exit' för att avsluta)")

    while True:
        query = input(f"> ")
        if query.lower() == 'exit':
            print("Avslutar programmet.")
            break

        with Live('', console=console, vertical_overflow='visible') as live:
            async with agent.run_stream(query, message_history=history, deps=user) as result:
                async for message in result.stream():
                    live.update(Markdown(message))
                await result.get_output()

        history = result.all_messages()
        print()

# --- Main entry point ---
def main():
    asyncio.run(run())
