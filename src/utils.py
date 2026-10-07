from collections.abc import AsyncIterable


async def alist[T](x: AsyncIterable[T]) -> list[T]:
    return [val async for val in x]
