def refactor(string: str) -> str:
    """Приводит юниксовский формат указания пути к файлу к формату, используемому для указания модулей в Python"""
    return string.replace("/", ".").replace("\\", ".").replace(".py", "")
