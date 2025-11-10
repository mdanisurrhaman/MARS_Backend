import numpy as np
from crewai.tools import tool
from typing import Dict, Any
import pandas as pd
import os
from io import StringIO
import json

class DataSchema:
    def __init__(self, data_path: str = "data/raw_data.csv"):
        self.data_path = data_path
        self.df = None

    def load_data(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"{self.data_path} does not exist")
        self.df = pd.read_csv(self.data_path)

    def get_info(self) -> str:
        if self.df is None:
            self.load_data()
        buffer = StringIO()
        self.df.info(buf=buffer)
        return buffer.getvalue()

    def get_column_types(self) -> Dict[str, list]:
        if self.df is None:
            self.load_data()

        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()

        return {
            "categorical_columns": cat_cols,
            "numerical_columns": num_cols
        }

    def get_summary(self) -> str:
        """Return schema summary as a JSON string."""
        if self.df is None:
            self.load_data()

        result = {
            "shape": self.df.shape,
            "column_types": self.get_column_types(),
            "info": self.get_info()
        }
        return json.dumps(result, indent=2)

    def as_text(self) -> str:
        """Return schema summary as a readable plain text string."""
        if self.df is None:
            self.load_data()

        column_types = self.get_column_types()
        return (
            f"DATASET SUMMARY\n"
            f"===============\n"
            f"Shape: {self.df.shape}\n\n"
            f"Categorical Columns: {column_types['categorical_columns']}\n"
            f"Numerical Columns: {column_types['numerical_columns']}\n\n"
            f"Schema Info:\n{self.get_info()}"
        )


@tool("load_user_data")
def load_user_data(dataset_path: str) -> str:
    """
    Loads the dataset from a given path (CSV, JSON, or Excel),
    and saves it as 'data/raw_data.csv' for downstream tasks.
    Returns a string summary.
    """

    os.makedirs("data", exist_ok=True)
    raw_data_path = "data/raw_data.csv"

    # Delete existing file if it exists
    if os.path.exists(raw_data_path):
        os.remove(raw_data_path)

    try:
        if dataset_path.endswith(".csv"):
            df = pd.read_csv(dataset_path)
        elif dataset_path.endswith(".json"):
            df = pd.read_json(dataset_path)
        elif dataset_path.endswith(".xlsx") or dataset_path.endswith(".xls"):
            df = pd.read_excel(dataset_path)
        else:
            return "Unsupported file format. Please provide CSV, JSON, or Excel."

        df.to_csv(raw_data_path, index=False)
        return (
            f"Data loaded successfully.\n"
            f"Rows: {df.shape[0]}, Columns: {df.shape[1]}\n"
            f"Saved to: {raw_data_path}"
        )

    except Exception as e:
        return f"Failed to load data: {str(e)}"


@tool("generate_schema")
def generate_schema(_: str = "") -> str:
    """
    Loads 'data/raw_data.csv' and returns a plain text schema summary
    (shape, column types, and df.info()).
    """
    try:
        schema = DataSchema()
        return schema.as_text()
    except Exception as e:
        return f"Error generating schema: {str(e)}"
