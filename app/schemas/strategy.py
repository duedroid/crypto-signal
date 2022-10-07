from pydantic import BaseModel


class CreateStrategySchema(BaseModel):
    key: str
    name: str
    timeframe: str