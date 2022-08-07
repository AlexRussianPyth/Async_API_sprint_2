from glob import glob

from utils.format import refactor

# Загружает все файлы из папки с фикстурами
pytest_plugins = [
    refactor(fixture) for fixture in glob("fixtures/*.py")
]
