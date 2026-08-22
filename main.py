from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI()


class ItemCreate(BaseModel):
    name: str
    price: float = Field(gt=0)


class Item(ItemCreate):
    id: int


class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id


@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"item {exc.item_id} not found"},
    )


items: dict[int, Item] = {}
next_id = 1


def pagination_params(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    global next_id
    new_item = Item(id=next_id, **item.model_dump())
    items[next_id] = new_item
    next_id += 1
    return new_item


@app.get("/items", response_model=list[Item])
async def list_items(pagination: dict = Depends(pagination_params)):
    values = list(items.values())
    return values[pagination["skip"] : pagination["skip"] + pagination["limit"]]


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    if item_id not in items:
        raise ItemNotFoundError(item_id)
    return items[item_id]


@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate):
    if item_id not in items:
        raise ItemNotFoundError(item_id)
    updated = Item(id=item_id, **item.model_dump())
    items[item_id] = updated
    return updated


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    if item_id not in items:
        raise ItemNotFoundError(item_id)
    del items[item_id]
