from fastapi import APIRouter

from agent.parser_agent import ParserChain

router = APIRouter()


@router.post("/parse")
async def parse_site(
        input_text: str,

):
    chain = ParserChain()
    return await chain.run(input_text=input_text)
