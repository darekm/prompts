import asyncio
import random
import logging
from typing import Any

from pydantic import BaseModel

from agents import Agent, AgentHooks, RunContextWrapper, Runner, Tool, function_tool
from agent_files import FinalPost,file_generator,get_post_md,print_file_md

logger = logging.getLogger("myagents")

class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        print(f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended with output {output}"
        )

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {source.name} handed off to {agent.name}"
        )

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started tool {tool.name}"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended tool {tool.name} with result {result}"
        )


###


@function_tool
def random_number(max: int) -> int:
    """
    Generate a random number up to the provided maximum.
    """
    return random.randint(0, max)


@function_tool
def multiply_by_two(x: int) -> int:
    """Simple multiplication by two."""
    return x * 2


class FinalResult(BaseModel):
    number: int


multiply_agent = Agent(
    name="Multiply Agent",
    instructions="Multiply the number by 2 and then return the final result.",
    tools=[multiply_by_two],
    output_type=FinalResult,
    hooks=CustomAgentHooks(display_name="Multiply Agent"),
)

transpose_agent = Agent(
    name="Transpose Agent",
    instructions="Transpose the input: set first line of body.",
    tools=[print_file_md],
    output_type=FinalPost,
    hooks=CustomAgentHooks(display_name="Transpose Agent"),
)
start_agent = Agent(
    name="Start Agent",
    instructions="Get name of file from directory. If it's name is ok with given mask hand off to the transpose agent.",
    tools=[get_post_md],
    output_type=FinalPost,
    handoffs=[transpose_agent],
    hooks=CustomAgentHooks(display_name="Start Agent"),
)



def initialise():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(name)s - %(levelname)s - %(message)s")
    logger.setLevel(logging.INFO)
    logging.getLogger("openai.agents").setLevel(logging.INFO)

async def main() -> None:
    user_input = input("Enter a max number: ")
    await Runner.run(
        start_agent,
        input=f"Find names begin with mask: {user_input}.",
    )

    print("Done!")


if __name__ == "__main__":
    initialise()
    asyncio.run(main())
"""
$ python examples/basic/agent_lifecycle_example.py

Enter a max number: 250
### (Start Agent) 1: Agent Start Agent started
### (Start Agent) 2: Agent Start Agent started tool random_number
### (Start Agent) 3: Agent Start Agent ended tool random_number with result 37
### (Start Agent) 4: Agent Start Agent started
### (Start Agent) 5: Agent Start Agent handed off to Multiply Agent
### (Multiply Agent) 1: Agent Multiply Agent started
### (Multiply Agent) 2: Agent Multiply Agent started tool multiply_by_two
### (Multiply Agent) 3: Agent Multiply Agent ended tool multiply_by_two with result 74
### (Multiply Agent) 4: Agent Multiply Agent started
### (Multiply Agent) 5: Agent Multiply Agent ended with output number=74
Done!
"""