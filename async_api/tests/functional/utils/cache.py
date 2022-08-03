async def generate_cache_key(index: str, separator: str = "::", **kwargs) -> str:
    """Возвращает строку для кеширования на основе набора аргументов"""

    keys = [index]

    for arg in sorted(kwargs):
        if kwargs[arg] is not None:
            keys.append(str(arg))
            keys.append(str(kwargs[arg]))

    return separator.join(keys)