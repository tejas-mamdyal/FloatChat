import os
import xarray as xr
import pandas as pd
import numpy as np

# Use paths relative to script location or environment variables
BASE_DIR = os.getenv("APP_BASE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
SOURCE_FOLDER = os.getenv("SOURCE_FOLDER", os.path.join(BASE_DIR, "downloads"))
DESTINATION_FOLDER = os.getenv("DESTINATION_FOLDER", os.path.join(BASE_DIR, "downloads", "parquet"))

def convert_netcdf_to_parquet(source_folder, destination_folder):
    """
    Converts all NetCDF files in the source folder to Parquet format.
    Each Parquet file will include all profiles, levels, variables, and metadata.
    """
    # Ensure destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    # Get all NetCDF files
    nc_files = [f for f in os.listdir(source_folder) if f.endswith(".nc")]
    if not nc_files:
        print("No NetCDF files found in source folder.")
        return

    for nc_file in nc_files:
        nc_path = os.path.join(source_folder, nc_file)
        print(f"\nProcessing file: {nc_path}")

        try:
            # Open dataset
            ds = xr.open_dataset(nc_path)

            # Extract dimensions
            num_profiles = ds.dims.get("N_PROF", 1)
            num_levels = ds.dims.get("N_LEVELS", 1)

            # Build a base index: profile_id x level_id
            profile_idx = np.arange(num_profiles)
            level_idx = np.arange(num_levels)

            index = pd.MultiIndex.from_product(
                [profile_idx, level_idx],
                names=["profile_id", "level_id"]
            )

            # Create base dataframe
            df = pd.DataFrame(index=index).reset_index()

            # --------------------------------------------------------
            # Add key coordinate variables (LAT, LON, JULD, etc.)
            # --------------------------------------------------------
            coord_vars = ["LATITUDE", "LONGITUDE", "JULD"]
            for coord in coord_vars:
                if coord in ds.variables:
                    data = ds[coord].values
                    # These are per profile, so repeat for each level
                    expanded = np.repeat(data, num_levels)
                    df[coord.lower()] = expanded

            # --------------------------------------------------------
            # Add core measurement variables
            # --------------------------------------------------------
            core_vars = ["PRES", "TEMP", "PSAL"]
            for var in core_vars:
                if var in ds.variables:
                    data = ds[var].values  # Shape (N_PROF, N_LEVELS)
                    df[var.lower()] = data.flatten()

            # --------------------------------------------------------
            # Add adjusted versions if available
            # --------------------------------------------------------
            adjusted_vars = ["PRES_ADJUSTED", "TEMP_ADJUSTED", "PSAL_ADJUSTED"]
            for var in adjusted_vars:
                if var in ds.variables:
                    df[var.lower()] = ds[var].values.flatten()

            # --------------------------------------------------------
            # Add QC flags (quality control)
            # --------------------------------------------------------
            qc_vars = ["PRES_QC", "TEMP_QC", "PSAL_QC"]
            for var in qc_vars:
                if var in ds.variables:
                    df[var.lower()] = ds[var].values.flatten()

            # --------------------------------------------------------
            # Add global attributes as constant metadata columns
            # --------------------------------------------------------
            for attr_name, attr_value in ds.attrs.items():
                df[f"global_{attr_name}"] = attr_value

            # --------------------------------------------------------
            # Save to Parquet
            # --------------------------------------------------------
            base_name = os.path.splitext(nc_file)[0]
            parquet_path = os.path.join(destination_folder, f"{base_name}.parquet")

            df.to_parquet(parquet_path, engine='pyarrow', index=False)
            print(f"Saved to {parquet_path} (rows: {len(df)})")

        except Exception as e:
            print(f"Error processing {nc_file}: {e}")


if __name__ == "__main__":
    convert_netcdf_to_parquet(SOURCE_FOLDER, DESTINATION_FOLDER)
