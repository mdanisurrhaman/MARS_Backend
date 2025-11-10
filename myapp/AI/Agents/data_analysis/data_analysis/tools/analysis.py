import re
import pandas as pd
import numpy as np
from crewai.tools import tool
from typing import Any, Dict
import json
import os
from crewai import LLM
from dotenv import load_dotenv
from myapp.AI.Agents.data_analysis.data_analysis.tools.classifier import get_data_path_from_query

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

@tool("generate_and_execute_analysis")
def generate_and_execute_analysis(user_query: str) -> Dict[str, Any]:
    """
    Generate analysis code, execute it safely, and return results with code used.
    Selects dataset path based on user query, uses preprocessed or raw data accordingly.
    """

    try:
        # Dynamically resolve dataset path
        data_path = get_data_path_from_query(user_query)

        if not os.path.exists(data_path):
            return {
                "status": "error",
                "query": user_query,
                "error": f"Data file '{data_path}' not found",
                "code_used": "",
                "result": ""
            }

        # Load the data
        df = pd.read_csv(data_path)

        # Build enhanced schema context
        schema = _build_enhanced_schema(df, data_path)

        # Validate LLM availability
        if llm is None:
            return {
                "status": "error",
                "query": user_query,
                "error": "LLM not initialized",
                "code_used": "",
                "result": ""
            }

        # Generate analysis code with enhanced prompt
        code = _generate_analysis_code(user_query, schema)

        # Execute the generated code safely
        execution_result = _execute_code_safely(
            code=code,
            df=df,
            data_source=data_path,
            user_query=user_query
        )

        # Generate summary from query, actual result data, and code
        summary = generate_summary(user_query, execution_result.get("result", ""), code)
        execution_result["summary"] = summary

        return execution_result

    except Exception as e:
        return {
            "status": "error",
            "query": user_query,
            "error": str(e),
            "code_used": "",
            "result": ""
        }

def _build_enhanced_schema(df: pd.DataFrame, data_path: str) -> dict:
    """Build comprehensive schema information for better code generation."""
    
    # Basic schema
    schema = {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(str).to_dict(),
        "sample_data": df.head(3).to_dict(),
        "is_decoded": "decoded" in data_path.lower()
    }
    
    # Identify column types for better code generation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = []
    
    # Detect potential datetime columns
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated', 'timestamp']):
            datetime_cols.append(col)
    
    schema.update({
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "potential_datetime_columns": datetime_cols,
        "null_counts": df.isnull().sum().to_dict(),
        "unique_counts": {col: df[col].nunique() for col in df.columns if df[col].nunique() < 50}
    })
    
    return schema

def _generate_analysis_code(query: str, schema: dict) -> str:
    """Generate pandas analysis code using CrewAI LLM with enhanced prompt."""
    
    dataset_path = get_data_path_from_query(query)
    is_decoded = schema.get("is_decoded", False)
    prompt = f"""
        You are an expert Python data analyst with deep analytical thinking skills. 

        STEP 1: QUERY INTERPRETATION AND CRITICAL THINKING
        First, carefully analyze what the user is ACTUALLY asking for:

        Query: "{query}"
        dataset_path: "{dataset_path}"

        Ask yourself these critical questions:
        - What is the TRUE intent behind this query?
        - Are they asking for aggregate totals across multiple records, or characteristics of individual items?
        - Should I be looking at per-unit metrics or cumulative metrics?
        - What would be the most meaningful business insight to provide?
        - Are there any ambiguities that need clarification through the analysis approach?

        STEP 2: DATASET UNDERSTANDING
        - Shape: {schema.get('shape', 'Unknown')} rows × columns
        - Data Type: {'Decoded/Preprocessed' if is_decoded else 'Raw'} 
        - Columns: {schema.get('columns', [])}
        - Numeric Columns: {schema.get('numeric_columns', [])}
        - Categorical Columns: {schema.get('categorical_columns', [])}
        - Potential DateTime Columns: {schema.get('potential_datetime_columns', [])}
        - Sample Data: {schema.get('sample_data', {})}

        STEP 3: ANALYTICAL APPROACH DECISION
        Based on your interpretation:
        - If asking about "capacity" or "configuration" → Find the typical/maximum configuration per unit
        - If asking about "total volume" or "fleet performance" → Sum across all records
        - If asking about "best performing" → Consider appropriate metrics (per-unit vs aggregate)
        - If asking about "trends" → Group by time periods
        - If asking about "comparison" → Ensure fair comparison basis

        STEP 4: CODE IMPLEMENTATION RULES
        1. Use 'df' as the DataFrame variable (already loaded from "{dataset_path}")
        2. Return ONLY valid Python code (no comments, explanations, or ``` blocks)
        3. MANDATORY: End with 'result = your_final_analysis'
        4. For aircraft/vehicle capacity questions: Use .drop_duplicates() or .groupby().first() to get per-unit specs
        5. For datetime operations: pd.to_datetime(df['column']) first
        6. Create derived features when needed: df['total_seats'] = df['first'] + df['business'] + df['economy']
        7. Use appropriate aggregation: .sum(), .mean(), .max(), .count() based on query intent
        8. Sort results meaningfully: .sort_values(by='metric', ascending=False)
        9. Handle edge cases: .dropna(), .fillna() when appropriate
        10. Round decimals: .round(2) for clarity

        STEP 5: ADVANCED PATTERNS FOR COMPLEX QUERIES
        - Configuration/Specification queries: df.groupby('type')[specs].first() or .drop_duplicates(['type'])
        - Performance comparison: df.groupby('category').agg({{'metric': ['mean', 'max', 'std']}})
        - Time-based analysis: pd.to_datetime() + .dt accessor for temporal grouping
        - Multi-dimensional analysis: .pivot_table() with appropriate index/columns/values
        - Statistical analysis: .describe(), .quantile(), .corr() for deeper insights
        - Filtering complex conditions: df.query() or boolean indexing with multiple conditions

        CRITICAL EXAMPLES:
        - "Which car model has the highest fuel efficiency?" → Per-model spec, not total consumption
        - "What aircraft type carries the most passengers?" → Per-aircraft capacity, not fleet total
        - "Which product generates the most revenue?" → Could be per-unit or total, consider context
        - "Show sales trends over time" → Time-based aggregation of transaction data

        STEP 6: QUALITY CHECKS
        - Does the result answer the actual question being asked?
        - Is the aggregation level appropriate (per-unit vs total)?
        - Are the results sorted in a meaningful way?
        - Would this analysis provide actionable business insights?

        Now generate ONLY the executable pandas code that thoughtfully addresses the query:
        """

    try:
        result = llm.call(prompt)   #type: ignore
        
        # Clean the response more thoroughly
        code = re.sub(r'^```(?:python)?\s*', '', result, flags=re.MULTILINE)
        code = re.sub(r'```\s*$', '', code, flags=re.MULTILINE)
        code = code.replace("print(", "# print(")
        
        # Remove any explanatory text that might come before or after the code
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('"""') and not line.startswith("'''"):
                clean_lines.append(line)
        
        code = '\n'.join(clean_lines)
        return code.strip()
        
    except Exception as e:
        print(f"LLM call failed for analysis: {e}")
        return f"# Error generating code: {e}"

def _execute_code_safely(
    code: str,
    df: pd.DataFrame,
    *,
    data_source: str = "",
    user_query: str = ""
) -> dict:
    """Execute analysis code with safety restrictions."""

    # Security check
    if any(pattern in code.lower() for pattern in DANGEROUS_PATTERNS):
        print("Unsafe code detected")
        return {
            "status": "error",
            "query": user_query,
            "code_used": code,
            "result": "Unsafe code detected - execution blocked",
            "data_shape": list(df.shape),
            "data_source": os.path.basename(data_source)
        }

    try:
        safe_builtins = {
            'print': print, 'len': len, 'range': range,
            'min': min, 'max': max, 'sum': sum,
            'sorted': sorted, 'abs': abs, 'round': round,
            'str': str, 'int': int, 'float': float, 'list': list
        }

        context = {
            'df': df.copy(),
            'pd': pd,
            'np': np,
            **safe_builtins
        }

        # Execute code
        if '\n' in code or '=' in code:
            exec(code, context)
            # Look for result variables in order of preference
            for var_name in ['result', 'analysis_result', 'output', 'venue_stats', 'final_result']:
                if var_name in context:
                    result = context[var_name]
                    break
            else:
                # If no explicit result variable, check if df was modified
                if 'df' in context and not context['df'].equals(df):
                    result = context['df']
                else:
                    # Look for any DataFrame/Series variables created
                    for var_name, var_value in context.items():
                        if var_name not in ['df', 'pd', 'np'] and not var_name.startswith('__'):
                            if isinstance(var_value, (pd.DataFrame, pd.Series)) and len(var_value) > 0:
                                result = var_value
                                break
                    else:
                        result = "Code executed successfully - no output variable found"
        else:
            result = eval(code, context)

        # Format result
        result_display = _format_analysis_result(result)

        return {
            "status": "success",
            "query": user_query,
            "code_used": code,
            "result": result_display,
            "data_shape": list(df.shape),
            "data_source": os.path.basename(data_source)
        }

    except Exception as e:
        print(f"Code execution failed: {e}")
        return {
            "status": "error",
            "query": user_query,
            "code_used": code,
            "result": f"Execution Error: {str(e)}",
            "data_shape": list(df.shape),
            "data_source": os.path.basename(data_source)
        }

def _format_analysis_result(result: Any) -> str:
    """Format analysis result for user display."""
    if isinstance(result, pd.DataFrame):
        if len(result) > 20:
            return f"DataFrame with {len(result)} rows, {len(result.columns)} columns:\n{result.head(10).to_string()}\n... (showing first 10 rows)"
        else:
            return result.to_string()
    elif isinstance(result, pd.Series):
        if len(result) > 20:
            return f"Series with {len(result)} values:\n{result.head(10).to_string()}\n... (showing first 10 values)"
        else:
            return result.to_string()
    elif isinstance(result, (int, float)):
        return f"Result: {result}"
    else:
        return str(result)

def generate_summary(query: str, result_data: str, code: str = "") -> str:
    """Generate result summary."""
    
    if llm is None:
        return f"Analysis completed for: {query}. LLM not available for summary generation."
    
    prompt = f"""
You are a data analyst providing business insights. Based on the analysis results, provide a clear summary that:

1. Directly answers the user's question
2. Highlights key findings with specific numbers
3. Identifies important patterns or trends
4. Provides actionable business insights

Focus ONLY on insights and findings, not on methodology or code explanation.

User Query: {query}

Analysis Results:
{str(result_data)[:1500]}

Provide a concise 2-4 sentence summary with key insights:
"""

    try:
        summary = llm.call(prompt)
        return summary.strip()
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return f"Analysis completed for: {query}. Key results are shown above."


# Test function (uncomment to test)
# if __name__ == "__main__":
#     response = generate_and_execute_analysis("Tell me about the dataset.")
#     print(json.dumps(response, indent=2))