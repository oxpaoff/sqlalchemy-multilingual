from setuptools import setup, find_packages

setup(
    packages=find_packages(
        where=[
            "src/sqlalchemy-multilingual",
            "src/sqlalchemy-multilingual/alembic"
        ],
        exclude=[".venv"]
    ),
)
