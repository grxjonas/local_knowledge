import os
from dotenv import load_dotenv
load_dotenv()
from pydantic_ai import Agent, RunContext
import asyncio
from pydantic_ai.mcp import MCPServerStreamableHTTP
# import logfire
# logfire.configure()
# logfire.instrument_pydantic_ai()
from rich.live import Live
from rich.markdown import CodeBlock, Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.console import Console, ConsoleOptions, RenderResult
from clients.prompts import cli_system_prompt, cli_instructions
from typing import TypedDict
import datetime
from zoneinfo import ZoneInfo

WHOAMI = os.getenv("WHOAMI","BI-Consultant at Hypergene AB")
class User(TypedDict):
    name: str
    current_time: str

def create_deps():
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Madrid"))
    return User(name=WHOAMI, current_time=now.isoformat())
user = create_deps()

CUSTOMER = os.getenv("CUSTOMER","Hypergene")

server = MCPServerStreamableHTTP("http://localhost:8051/mcp")

agent = Agent("gpt-4o-mini", mcp_servers=[server], 
              system_prompt=cli_system_prompt, deps_type = User)

@agent.system_prompt
def get_user_info(ctx: RunContext[User]):
    return f"Användaren är {ctx.deps["name"]}"

@agent.tool
def get_current_date_and_time(ctx: RunContext[User]) -> str:
    """ Dagens datum och aktuell tid """
    return f" Nuvarande datum och tid är: {ctx.deps["current_time"]}."

@agent.instructions
def get_format_instructions(ctx: RunContext[User])-> str:
    msgs = getattr(ctx, "messages", None)
    if msgs and len(msgs) > 0:
        return cli_instructions + f" Nuvarande datum och tid är: {ctx.deps["current_time"]}."
    else:
        return ""

def prettier_code_blocks():
    """Make rich code blocks prettier and easier to copy.

    From https://github.com/samuelcolvin/aicli/blob/v0.8.0/samuelcolvin_aicli.py#L22
    """

    class SimpleCodeBlock(CodeBlock):
        def __rich_console__(
            self, console: Console, options: ConsoleOptions
        ) -> RenderResult:
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

async def run():
    history = []
    prettier_code_blocks()
    console = Console()
    with Live('', console=console, vertical_overflow='visible') as live:
                    async with agent.run_stream(f"Jag är {user['name']}. Vilken underbar dag! Ge mig ett glad och överdrivet positiv hälsning för att höja stämningen ännu mer!", message_history = history, deps = user) as result:
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
                    async with agent.run_stream(query, message_history = history, deps = user) as result:
                        async for message in result.stream():
                            live.update(Markdown(message))
                        await result.get_output()
        history = result.all_messages()
        print()
def main():
    asyncio.run(run())