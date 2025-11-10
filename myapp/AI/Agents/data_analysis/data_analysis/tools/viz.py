import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
from crewai.tools import tool
from typing import Any, Dict, Tuple
import json
import os
from crewai import LLM
from dotenv import load_dotenv
from myapp.AI.Agents.data_analysis.data_analysis.tools.classifier import get_data_path_from_query
from datetime import datetime
import warnings

# Suppress future warnings
warnings.filterwarnings('ignore', category=FutureWarning)

load_dotenv()

# Initialize CrewAI LLM with error handling
try:
    llm = LLM(
        model="gemini/gemini-2.0-flash-001",  
        temperature=0
    )
except Exception as e:
    print(f"LLM initialization failed: {e}")
    llm = None

DANGEROUS_PATTERNS = [
    'import os', 'import sys', 'import subprocess', 'import socket',
    'eval(', 'exec(', '__import__', 'open(', 'file(', 'input(',
    'raw_input(', 'compile(', 'globals(', 'locals(', 'vars(',
    'dir(', 'hasattr(', 'getattr(', 'setattr(', 'delattr('
]

# Create output folder if it doesn't exist
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@tool("generate_and_execute_visualization")
def generate_and_execute_visualization(user_query: str) -> Dict[str, Any]:
    """
    Generate visualization code using Plotly, Matplotlib, or Seaborn based on query requirements.
    Uses intelligent dataset selection and provides insights from visualized data.
    Saves visualizations to output folder with datetime stamps.
    """
    
    try:
        # Get appropriate data path using your existing logic
        data_path = get_data_path_from_query(user_query)
        
        if not os.path.exists(data_path):
            return {
                "status": "error",
                "query": user_query,
                "error": f"Data file '{data_path}' not found",
                "code_used": "",
                "visualization": None,
                "visualization_path": None,
                "data_used": "",
                "insights": ""
            }

        # Load the data
        df = pd.read_csv(data_path)
        
        # Build schema for visualization
        schema = _build_viz_schema(df, data_path)
        
        # Validate LLM availability
        if llm is None:
            return {
                "status": "error",
                "query": user_query,
                "error": "LLM not initialized",
                "code_used": "",
                "visualization": None,
                "visualization_path": None,
                "data_used": os.path.basename(data_path),
                "insights": ""
            }

        # Generate visualization code
        viz_code, viz_library = _generate_visualization_code(user_query, schema)
        
        # Execute the visualization code
        execution_result = _execute_viz_code_safely(
            code=viz_code,
            df=df,
            viz_library=viz_library,
            user_query=user_query,
            data_source=data_path
        )
        
        # Generate insights from the visualization data
        if execution_result["status"] == "success" and execution_result.get("filtered_data") is not None:
            insights = _generate_viz_insights(
                user_query, 
                execution_result["filtered_data"], 
                viz_library
            )
            execution_result["insights"] = insights
        
        return execution_result

    except Exception as e:
        return {
            "status": "error",
            "query": user_query,
            "error": str(e),
            "code_used": "",
            "visualization": None,
            "visualization_path": None,
            "data_used": "",
            "insights": ""
        }

def _build_viz_schema(df: pd.DataFrame, data_path: str) -> dict:
    """Build schema information optimized for visualization generation."""
    
    schema = {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(str).to_dict(),
        "sample_data": df.head(3).to_dict(),
        "is_decoded": "decoded" in data_path.lower()
    }
    
    # Identify column types for better viz generation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = []
    
    # Detect potential datetime columns
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated', 'timestamp']):
            datetime_cols.append(col)
    
    # Get unique value counts for categorical columns (for better chart selection)
    categorical_info = {}
    for col in categorical_cols:
        unique_count = df[col].nunique()
        if unique_count <= 20:  # Only for manageable categories
            categorical_info[col] = {
                "unique_count": unique_count,
                "top_values": df[col].value_counts().head(10).to_dict()
            }
    
    schema.update({
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "potential_datetime_columns": datetime_cols,
        "categorical_info": categorical_info,
        "data_ranges": {col: [df[col].min(), df[col].max()] for col in numeric_cols}
    })
    
    return schema

def _generate_visualization_code(query: str, schema: dict) -> Tuple[str, str]:
    """Generate visualization code and determine which library to use."""

    prompt = f"""
    You are an expert data visualization developer. Generate ONLY executable Python code for creating visualizations.

    CRITICAL: First understand what the query is ACTUALLY asking:
    - Query: "{query}"
    - Are they asking for per-item specifications OR aggregate totals across records?
    - Should I compare individual characteristics OR cumulative performance?
    - What aggregation method makes business sense: .sum(), .mean(), .max(), .first()?

    COMMON ANALYSIS MISTAKES TO AVOID:
    - Summing individual specifications across multiple records
    - Using wrong aggregation when specs vs totals are different concepts
    - Inappropriate time groupings or comparing incompatible metrics
    - For specifications/capacity: use .groupby().max() or .drop_duplicates()
    - For performance/volume totals: use .groupby().sum() or .mean()

    Choose the BEST library for the visualization:
    - *Plotly*: Interactive charts, dashboards, 3D plots, hover info, web-friendly
    - *Matplotlib*: Statistical plots, publication-quality, fine control, subplots
    - *Seaborn*: Statistical visualizations, distributions, correlations, beautiful defaults

    DATASET INFORMATION:
    - Shape: {schema.get('shape', 'Unknown')} rows × columns
    - Data Type: {'Decoded/Preprocessed' if schema.get('is_decoded') else 'Raw'} 
    - Columns: {schema.get('columns', [])}
    - Numeric Columns: {schema.get('numeric_columns', [])}
    - Categorical Columns: {schema.get('categorical_columns', [])}
    - DateTime Columns: {schema.get('potential_datetime_columns', [])}
    - Sample Data: {schema.get('sample_data', {})}

    CODING RULES:
    1. Use 'df' as the DataFrame variable (already loaded)
    2. Return ONLY valid Python code (no comments, explanations, or  blocks)
    3. ALWAYS assign filtered/processed data to 'filtered_data' variable
    4. ALWAYS assign final figure to 'fig' variable
    5. Choose ONE library per visualization:
    - For Plotly: import plotly.express as px, plotly.graph_objects as go
    - For Matplotlib: import matplotlib.pyplot as plt
    - For Seaborn: import seaborn as sns, matplotlib.pyplot as plt

    ANALYSIS PATTERNS:
    - Individual specifications: filtered_data = df.groupby('type_column')['spec_column'].max()
    - Volume/totals: filtered_data = df.groupby('category_column')['total_column'].sum()
    - Performance averages: filtered_data = df.groupby('group_column')['metric_column'].mean()
    - Time trends: filtered_data = df.groupby('time_period')['value_column'].appropriate_agg()

    VISUALIZATION PATTERNS:
    - Bar/Column Charts: Top N analysis, category comparisons
    - Line Charts: Time series, trends over time
    - Scatter Plots: Correlations, relationships between variables  
    - Histograms: Distributions, frequency analysis
    - Heatmaps: Correlations, cross-tabulations
    - Box Plots: Statistical summaries, outlier detection

    CODE STRUCTURE:
    python
    # Data filtering/processing with CORRECT analysis (assign to filtered_data)
    filtered_data = df.groupby('category')['metric'].appropriate_method()

    # Create visualization (assign to fig)
    fig = px.bar(filtered_data, x='col1', y='col2', title='Descriptive Title')
    ```

    Generate executable visualization code with correct analysis:
    """

    try:
        result = llm.call(prompt)  #type: ignore
        
        # Clean the response
        code = re.sub(r'^```(?:python)?\s*', '', result, flags=re.MULTILINE)
        code = re.sub(r'```\s*$', '', code, flags=re.MULTILINE)
        
        # Detect library being used
        viz_library = "plotly"  # default
        if "matplotlib.pyplot" in code or "plt." in code:
            if "seaborn" in code or "sns." in code:
                viz_library = "seaborn"
            else:
                viz_library = "matplotlib"
        elif "plotly" in code or "px." in code or "go." in code:
            viz_library = "plotly"
        
        return code.strip(), viz_library
        
    except Exception as e:
        print(f"LLM call failed for visualization: {e}")
        return f"# Error generating visualization code: {e}", "plotly"

def _execute_viz_code_safely(
    code: str,
    df: pd.DataFrame,
    viz_library: str,
    user_query: str,
    data_source: str
) -> dict:
    """Execute visualization code safely and return results."""
    
    # Security check
    if any(pattern in code.lower() for pattern in DANGEROUS_PATTERNS):
        return {
            "status": "error",
            "query": user_query,
            "code_used": code,
            "error": "Unsafe code detected - execution blocked",
            "visualization": None,
            "visualization_path": None,
            "data_used": os.path.basename(data_source),
            "library_used": viz_library,
            "filtered_data": None
        }

    try:
        # Prepare execution context
        context = {
            'df': df.copy(),
            'pd': pd,
            'np': np,
            'px': px,
            'go': go,
            'plt': plt,
            'sns': sns
        }
        
        # Execute the code
        exec(code, context)
        
        # Extract results
        fig = context.get('fig')
        filtered_data = context.get('filtered_data', df)
        
        if fig is None:
            return {
                "status": "error",
                "query": user_query,
                "code_used": code,
                "error": "No 'fig' variable found in generated code",
                "visualization": None,
                "visualization_path": None,
                "data_used": os.path.basename(data_source),
                "library_used": viz_library,
                "filtered_data": filtered_data
            }
        
        # Save visualization to file and get path
        viz_output, viz_path = _save_and_convert_visualization(fig, viz_library, user_query)
        
        return {
            "status": "success",
            "query": user_query,
            "code_used": code,
            "visualization": viz_output,
            "visualization_path": viz_path,
            "data_used": f"{os.path.basename(data_source)} ({'decoded/preprocessed' if 'decoded' in data_source else 'raw'})",
            "library_used": viz_library,
            "data_shape": list(df.shape),
            "filtered_data_info": {
                "shape": list(filtered_data.shape),
                "columns": list(filtered_data.columns),
                "sample": filtered_data.head(3).to_dict() if not filtered_data.empty else {}
            },
            "filtered_data": filtered_data,  # Keep original for internal use
            "data_note": "To use raw data instead, specify 'use raw data' in your query"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "query": user_query,
            "code_used": code,
            "error": f"Execution Error: {str(e)}",
            "visualization": None,
            "visualization_path": None,
            "data_used": os.path.basename(data_source),
            "library_used": viz_library,
            "filtered_data": None
        }

def _save_and_convert_visualization(fig, viz_library: str, user_query: str) -> tuple:
    """Save visualization to file and convert to appropriate output format."""
    
    # Generate timestamp and sanitize query for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = re.sub(r'[^\w\s-]', '', user_query.replace(' ', '_'))[:50]
    
    if viz_library == "plotly":
        # Save as HTML first (primary format for Plotly)
        html_filename = f"viz_{timestamp}_{safe_query}.html"
        html_path = os.path.join(OUTPUT_FOLDER, html_filename)
        
        try:
            fig.write_html(html_path, include_plotlyjs='cdn')
            
            # Also try to save as PNG (fallback)
            png_filename = f"viz_{timestamp}_{safe_query}.png"
            png_path = os.path.join(OUTPUT_FOLDER, png_filename)
            
            try:
                # Requires kaleido: pip install kaleido
                fig.write_image(png_path, format='png', width=1200, height=800)
                viz_path = {"html": html_path, "png": png_path}
            except Exception as png_error:
                print(f"PNG export failed (install kaleido for PNG support): {png_error}")
                viz_path = {"html": html_path, "png": None}
            
            # Return Plotly JSON for interactive display
            viz_output = {
                "type": "plotly",
                "data": fig.to_dict() if hasattr(fig, 'to_dict') else str(fig)
            }
            
            # Uncomment the line below to default to HTML file path instead of interactive JSON
            # viz_output = {"type": "html_file", "path": html_path}
            
            return viz_output, viz_path
            
        except Exception as e:
            print(f"Failed to save Plotly visualization: {e}")
            return {"type": "error", "data": str(e)}, None
    
    elif viz_library in ["matplotlib", "seaborn"]:
        # Save as PNG
        png_filename = f"viz_{timestamp}_{safe_query}.png"
        png_path = os.path.join(OUTPUT_FOLDER, png_filename)
        
        try:
            if hasattr(fig, 'savefig'):
                # fig is a Figure object
                fig.savefig(png_path, format='png', dpi=300, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
            else:
                # Use plt.savefig
                plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
            
            # Convert to base64 for display
            with open(png_path, 'rb') as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode()
            
            plt.close('all')  # Clean up
            
            viz_output = {
                "type": "image",
                "data": f"data:image/png;base64,{image_base64}"
            }
            
            return viz_output, {"png": png_path}
            
        except Exception as e:
            print(f"Failed to save matplotlib/seaborn visualization: {e}")
            plt.close('all')  # Clean up even on error
            return {"type": "error", "data": str(e)}, None
    
    return {"type": "unknown", "data": str(fig)}, None

def _generate_viz_insights(user_query: str, filtered_data: pd.DataFrame, viz_library: str) -> str:
    """Generate insights from the visualized data."""
    
    if llm is None:
        return f"Visualization created for: {user_query}. LLM not available for insights generation."
    
    # Prepare data summary for insights
    data_summary = {
        "shape": filtered_data.shape,
        "columns": list(filtered_data.columns),
        "numeric_summary": filtered_data.describe().to_dict() if len(filtered_data.select_dtypes(include=[np.number]).columns) > 0 else {},
        "categorical_counts": {col: filtered_data[col].value_counts().head(5).to_dict() 
                             for col in filtered_data.select_dtypes(include=['object']).columns[:3]}
    }
    
    prompt = f"""
Based on the data used in this visualization, provide key insights and patterns.

Query: {user_query}
Visualization Library: {viz_library}
Data Summary: {str(data_summary)[:1000]}

Provide 2-3 specific insights focusing on:
1. Key patterns or trends visible in the data
2. Notable values, outliers, or distributions
3. Business implications or actionable findings

Keep insights concise and data-driven with specific numbers when relevant:
"""

    try:
        insights = llm.call(prompt)
        return insights.strip()
    except Exception as e:
        return f"Visualization created successfully. Insights generation failed: {str(e)}"


# Test function (uncomment to test)
# if __name__ == "__main__":
#     result = generate_and_execute_visualization("How many matches were played per date?")
    
#     # Create a JSON-safe version of the result for printing
#     json_safe_result = {}
#     for k, v in result.items():
#         if k == 'visualization':
#             continue  # Skip visualization data
#         elif k == 'filtered_data' and v is not None:
#             # Convert DataFrame to summary info
#             json_safe_result[k] = {
#                 "shape": list(v.shape),
#                 "columns": list(v.columns),
#                 "sample": v.head(3).to_dict() if not v.empty else {}
#             }
#         else:
#             json_safe_result[k] = v
    
#     print(json.dumps(json_safe_result, indent=2))