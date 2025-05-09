from setuptools import setup, find_packages

setup(
    name="maritime-simulation",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "searoute-py==1.0.0",
        "pyais==1.7.0",
        "websockets==11.0.3",
        "pandas==2.1.0",
        "sqlalchemy==2.0.20",
        "geopandas==0.14.0",
        "pytest==7.4.2",
        "python-dotenv==1.0.0",
        "fastapi==0.103.1",
        "uvicorn==0.23.2",
        "shapely==2.0.1",
        "numpy==1.24.3",
        "pyproj==3.6.1",
    ],
) 