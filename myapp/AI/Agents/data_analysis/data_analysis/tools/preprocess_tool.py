import json
import os
import pandas as pd
import numpy as np
from crewai.tools import tool
from typing import Dict, Any
import warnings

@tool("preprocess_and_save_data")
def preprocess_and_save_data() -> Dict[str, Any]:
    """
    Cleans and prepares the raw dataset for analysis:
    - Fills missing values (mean for numerics, mode for categoricals)
    - Converts datetime-like columns to numeric timestamps
    - Encodes categorical columns using .cat.codes
    - Saves cleaned numeric data to 'data/preprocessed_data.csv'
    - Decodes categorical columns back to original values and saves to 'data/decoded.csv'
    - Returns mappings for datetime columns and category encodings
    """

    try:
        # Load raw data
        df = pd.read_csv("data/raw_data.csv")
        processed_df = df.copy()

        # Store mappings
        datetime_converted_columns = {}
        categorical_mappings = {}

        # 1. Handle missing values
        try:
            for col in processed_df.columns:
                if processed_df[col].dtype in ["int64", "float64"]:
                    if processed_df[col].isnull().any():
                        # FIXED: Use direct assignment instead of chained inplace operation
                        processed_df[col] = processed_df[col].fillna(processed_df[col].mean())
                else:
                    if processed_df[col].isnull().any():
                        mode_val = processed_df[col].mode().iloc[0] if not processed_df[col].mode().empty else "Unknown"
                        # FIXED: Use direct assignment instead of chained inplace operation
                        processed_df[col] = processed_df[col].fillna(mode_val)
        except Exception as e:
            print(f"Error filling missing values: {e}")

        # 2. Convert likely datetime columns and create datetime features
        try:
            datetime_features_created = {}
            
            for col in processed_df.columns:
                # Skip if already numeric
                if processed_df[col].dtype in ["int64", "float64"]:
                    continue
                    
                try:
                    # FIXED: Suppress the specific datetime format warning
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message="Could not infer format.*")
                        # Try to convert to datetime with more flexible approach
                        converted = pd.to_datetime(processed_df[col], errors="coerce")
                    
                    # Check if conversion was meaningful (more than 50% successful)
                    success_rate = converted.notna().sum() / len(converted)
                    
                    if success_rate > 0.5:  # If more than 50% converted successfully
                        # Create new datetime feature columns
                        new_cols = []
                        
                        # Add year, month, day for trend analysis
                        processed_df[f"{col}_year"] = converted.dt.year
                        processed_df[f"{col}_month"] = converted.dt.month
                        processed_df[f"{col}_day"] = converted.dt.day
                        processed_df[f"{col}_weekday"] = converted.dt.weekday
                        
                        # Add time components if time info exists
                        if converted.dt.hour.notna().any() and converted.dt.hour.sum() > 0:
                            processed_df[f"{col}_hour"] = converted.dt.hour
                            new_cols.append(f"{col}_hour")
                        
                        new_cols.extend([f"{col}_year", f"{col}_month", f"{col}_day", f"{col}_weekday"])
                        
                        # Store info about what was created
                        datetime_converted_columns[col] = {
                            "original_dtype": str(df[col].dtype),
                            "new_columns_created": new_cols,
                            "success_rate": success_rate,
                            "sample_original": str(df[col].iloc[0]) if len(df) > 0 else "N/A"
                        }
                        
                        datetime_features_created[col] = new_cols
                                                
                except Exception as conv_error:
                    print(f"Could not convert {col} to datetime: {conv_error}")
                    continue
                    
        except Exception as e:
            print(f"Error converting datetime columns: {e}")

        # 3. Encode categorical columns
        try:
            # Get remaining object columns
            cat_cols = processed_df.select_dtypes(include="object").columns.tolist()
            
            for col in cat_cols:
                try:
                    # Store original categories before encoding
                    processed_df[col] = processed_df[col].astype("category")
                    categorical_mappings[col] = {
                        "categories": processed_df[col].cat.categories.tolist(),
                        "original_dtype": "object"
                    }
                    
                    # Encode to numeric codes
                    processed_df[col] = processed_df[col].cat.codes
                                        
                except Exception as e:
                    print(f"Error encoding column {col}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error encoding categorical columns: {e}")

        # 4. Final data validation
        try:
            # Ensure all columns are numeric
            for col in processed_df.columns:
                if not pd.api.types.is_numeric_dtype(processed_df[col]):
                    # print(f"Warning: {col} is not numeric, attempting conversion")
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
                    
        except Exception as e:
            print(f"Error in final validation: {e}")

        # 5. Remove previous preprocessed file if exists
        processed_path = "data/preprocessed_data.csv"
        if os.path.exists(processed_path):
            os.remove(processed_path)

        # 6. Save processed data
        processed_df.to_csv(processed_path, index=False)
        
        # 7. Save mappings to JSON files in data folder
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Define all file paths
            categorical_mappings_path = "data/categorical_mappings.json"
            datetime_mappings_path = "data/datetime_mappings.json"
            
            # Remove existing JSON files if they exist
            for json_path in [categorical_mappings_path, datetime_mappings_path]:

                if os.path.exists(json_path):
                    os.remove(json_path)
                    # print(f"Removed existing file: {json_path}")
            
            # Save categorical mappings
            with open(categorical_mappings_path, 'w') as f:
                json.dump(categorical_mappings, f, indent=2)

            
            # Save datetime mappings
            with open(datetime_mappings_path, 'w') as f:
                json.dump(datetime_converted_columns, f, indent=2)
            
            
        except Exception as e:
            print(f"Error saving mappings to JSON files: {e}")

        # 8. NEW: Decode categorical columns back and save as decoded.csv
        decoded_columns = []
        decoding_status = "success"
        decoding_message = ""
        
        try:
            decoded_df = processed_df.copy()
            
            # Decode each categorical column back to original values
            for col, mapping_info in categorical_mappings.items():
                try:
                    categories = mapping_info['categories']
                    
                    # Convert encoded values back to original categories
                    decoded_values = []
                    for code in decoded_df[col]:
                        if pd.isna(code) or code == -1:
                            decoded_values.append(pd.NA)
                        elif 0 <= code < len(categories):
                            decoded_values.append(categories[int(code)])
                        else:
                            decoded_values.append(f"Unknown_Code_{code}")
                    
                    decoded_df[col] = decoded_values
                    decoded_columns.append(col)
                    
                except Exception as e:
                    print(f"Error decoding column {col}: {e}")
                    continue
            
            # Remove existing decoded file if it exists
            decoded_path = "data/decoded.csv"
            if os.path.exists(decoded_path):
                os.remove(decoded_path)
            
            # Save decoded data
            decoded_df.to_csv(decoded_path, index=False)
            decoding_message = f"Successfully decoded {len(decoded_columns)} categorical columns"
            
        except Exception as e:
            decoding_status = "error"
            decoding_message = f"Error during decoding: {str(e)}"
            decoded_path = None

        result: Dict[str, Any] = {
            "status": "success",
            "message": "Preprocessing completed and decoded data saved to decoded.csv",
            "original_shape": list(df.shape),
            "processed_shape": list(processed_df.shape),
            "datetime_converted_columns": datetime_converted_columns,
            "datetime_features_created": datetime_features_created,
            # "categorical_mappings": categorical_mappings,
            "total_columns": len(processed_df.columns),
            "files_created": [
                "data/preprocessed_data.csv",
                "data/categorical_mappings.json", 
                "data/datetime_mappings.json"
            ],
            # NEW: Decoding information
            "decoding_status": decoding_status,
            "decoding_message": decoding_message,
            "decoded_columns": decoded_columns,
            "total_decoded_columns": len(decoded_columns)
        }
        
        # Add decoded file to files_created if successful
        if decoding_status == "success" and decoded_path:
            result["files_created"].append("data/decoded.csv")

        return json.dumps(result, indent=2)
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred during preprocessing: {e}",
            "datetime_converted_columns": {},
            "categorical_mappings": {}
        }