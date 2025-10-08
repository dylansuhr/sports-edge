from setuptools import setup, find_packages

setup(
    name="sports-edge-models",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.3.0",
        "xgboost>=2.0.0",
        "statsmodels>=0.14.0",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "psycopg2-binary>=2.9.0",
        "sqlalchemy>=2.0.0",
    ],
)
