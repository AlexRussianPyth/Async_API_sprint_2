async def generate_cache_key(index: str, **kwargs) -> str:
    """Возвращает строку для кеширования на основе аргументов"""

    keys = [index]

    for arg in sorted(kwargs):
        if kwargs[arg] is not None:
            keys.append(str(arg))
            keys.append(str(kwargs[arg]))

    return "::".join(keys)
