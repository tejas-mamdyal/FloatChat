from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from netCDF4 import Dataset
from sklearn.linear_model import LinearRegression
import requests
import yaml
import os
import asyncio

router = APIRouter()

# Load configuration
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    raise HTTPException(status_code=500, detail="config.yaml not found")

GROQ_API_KEY = config.get("groq_api_key") or os.getenv("GROQ_API_KEY")

# Pydantic models
class VariableStats(BaseModel):
    variable_name: str
    min_value: float
    max_value: float
    mean_value: float
    std_dev: float
    count: int
    trend: str

class FileStats(BaseModel):
    file_path: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    variables: List[VariableStats]
    processing_status: str

class AnalysisRequest(BaseModel):
    file_paths: List[str]

class AnalysisResponse(BaseModel):
    file_statistics: List[FileStats]
    summary: Dict[str, Any]

class LocationPoint(BaseModel):
    latitude: float
    longitude: float
    file_path: str
    file_name: str

class MapDataResponse(BaseModel):
    locations: List[LocationPoint]
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None

class InsightsRequest(BaseModel):
    query: str
    file_statistics: List[FileStats]

class InsightsResponse(BaseModel):
    insights: str
    query: str
    files_analyzed: int

def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
	cols_lower = {c.lower(): c for c in df.columns}
	for name in candidates:
		low = name.lower()
		if low in cols_lower:
			return cols_lower[low]
	return None


def read_netcdf_data(file_path: str):
    """Extract statistics and lat/lon; prefers Parquet if provided."""
    try:
        if file_path.endswith('.parquet') and os.path.exists(file_path):
            df = pd.read_parquet(file_path)
            lat_col = _find_col(df, ['LATITUDE', 'latitude', 'lat'])
            lon_col = _find_col(df, ['LONGITUDE', 'longitude', 'lon', 'lng'])
            lat = float(df[lat_col].dropna().iloc[0]) if lat_col and not df[lat_col].dropna().empty else None
            lon = float(df[lon_col].dropna().iloc[0]) if lon_col and not df[lon_col].dropna().empty else None
            variable_stats = []
            for col in df.columns:
                if col.lower() in ['latitude', 'longitude', 'juld', 'time', 'lat', 'lon', 'lng']:
                    continue
                series = df[col].replace([99999.0, -99999.0, 9.9692099683868690e+36], np.nan).astype(float)
                series = series[np.isfinite(series)]
                name_upper = col.upper()
                if 'TEMP' in name_upper:
                    series = series[(series >= -5.0) & (series <= 50.0)]
                elif 'PSAL' in name_upper:
                    series = series[(series >= 0.0) & (series <= 50.0)]
                elif 'PRES' in name_upper:
                    series = series[(series >= 0.0) & (series <= 11000.0)]
                elif 'CHLA' in name_upper or 'CHL' in name_upper:
                    series = series[(series >= 0.0) & (series <= 100.0)]
                elif 'DOXY' in name_upper or 'OXYGEN' in name_upper:
                    series = series[(series >= 0.0) & (series <= 500.0)]
                elif 'NITRATE' in name_upper or 'NO3' in name_upper:
                    series = series[(series >= 0.0) & (series <= 100.0)]
                elif 'PH' in name_upper:
                    series = series[(series >= 6.0) & (series <= 9.0)]

                if series.size == 0:
                    continue
                variable_stats.append({
                    "name": col,
                    "mean": float(np.mean(series)),
                    "min": float(np.min(series)),
                    "max": float(np.max(series)),
                    "count": int(series.size)
                })

            return FileStats(
                file_path=file_path,
                latitude=lat,
                longitude=lon,
                variables=variable_stats,
                processing_status="success"
            )

        with Dataset(file_path, "r") as nc:
            stats = {}
            lat, lon = None, None

            if 'LATITUDE' in nc.variables:
                lat = float(nc.variables['LATITUDE'][0])
            if 'LONGITUDE' in nc.variables:
                lon = float(nc.variables['LONGITUDE'][0])

            # Time parsing
            time_data = []
            if "JULD" in nc.variables:
                base_date = datetime(1950, 1, 1)
                time_data = [base_date + timedelta(days=float(t)) for t in nc.variables["JULD"][:]]

            # Extract main variables
            core_vars = [v for v in nc.variables.keys() if v not in ["LATITUDE", "LONGITUDE", "JULD", "time"]]

            variable_stats = []
            for var in core_vars:
                try:
                    data = np.array(nc.variables[var][:]).flatten()
                    
                    # Filter out fill values, NaN, and apply reasonable bounds for ocean variables
                    data = data[np.isfinite(data)]
                    
                    # Remove common NetCDF fill values
                    data = data[data != 99999.0]  # Common fill value
                    data = data[data != -99999.0]  # Negative fill value
                    data = data[data != 9.9692099683868690e+36]  # Another common fill value
                    
                    # Apply reasonable bounds based on variable type
                    if 'TEMP' in var.upper():
                        # Ocean temperature bounds: -5°C to 50°C
                        data = data[(data >= -5.0) & (data <= 50.0)]
                    elif 'PSAL' in var.upper():
                        # Salinity bounds: 0 to 50 psu
                        data = data[(data >= 0.0) & (data <= 50.0)]
                    elif 'PRES' in var.upper():
                        # Pressure bounds: 0 to 11000 dbar (deepest ocean ~11km)
                        data = data[(data >= 0.0) & (data <= 11000.0)]
                    elif 'CHLA' in var.upper() or 'CHL' in var.upper():
                        # Chlorophyll bounds: 0 to 100 mg/m³
                        data = data[(data >= 0.0) & (data <= 100.0)]
                    elif 'DOXY' in var.upper() or 'OXYGEN' in var.upper():
                        # Dissolved oxygen bounds: 0 to 500 µmol/kg
                        data = data[(data >= 0.0) & (data <= 500.0)]
                    elif 'NITRATE' in var.upper() or 'NO3' in var.upper():
                        # Nitrate bounds: 0 to 100 µmol/kg
                        data = data[(data >= 0.0) & (data <= 100.0)]
                    elif 'PH' in var.upper():
                        # pH bounds: 6.0 to 9.0
                        data = data[(data >= 6.0) & (data <= 9.0)]
                    
                    if len(data) == 0:
                        continue

                    var_stats = {
                        "min": float(np.min(data)),
                        "max": float(np.max(data)),
                        "mean": float(np.mean(data)),
                        "std_dev": float(np.std(data)),
                        "count": int(len(data))
                    }

                    # Detect trend
                    trend = "Stable"
                    if time_data and len(time_data) == len(data) and len(data) > 2:
                        try:
                            timestamps = np.array([t.timestamp() for t in time_data]).reshape(-1, 1)
                            lr = LinearRegression().fit(timestamps, data)
                            slope = lr.coef_[0]
                            trend = "Increasing" if slope > 0 else "Decreasing"
                        except Exception:
                            trend = "Stable"

                    variable_stats.append(VariableStats(
                        variable_name=var,
                        min_value=var_stats["min"],
                        max_value=var_stats["max"],
                        mean_value=var_stats["mean"],
                        std_dev=var_stats["std_dev"],
                        count=var_stats["count"],
                        trend=trend
                    ))

                except Exception as e:
                    continue

            return FileStats(
                file_path=file_path,
                latitude=lat,
                longitude=lon,
                variables=variable_stats,
                processing_status="success"
            )

    except Exception as e:
        return FileStats(
            file_path=file_path,
            latitude=None,
            longitude=None,
            variables=[],
            processing_status=f"error: {str(e)}"
        )

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_files(request: AnalysisRequest):
    """Analyze NetCDF files and return statistics"""
    
    if not request.file_paths:
        raise HTTPException(status_code=400, detail="No file paths provided")
    
    file_statistics = []
    total_vars = 0
    successful_files = 0
    
    # Deduplicate file paths to avoid redundant processing
    unique_paths = list(set(request.file_paths))
    
    for file_path in unique_paths:
        if not os.path.exists(file_path):
            file_stats = FileStats(
                file_path=file_path,
                latitude=None,
                longitude=None,
                variables=[],
                processing_status="file_not_found"
            )
        else:
            # Unblock the FastAPI event loop for heavy I/O and pandas processing
            file_stats = await asyncio.to_thread(read_netcdf_data, file_path)
            if file_stats.processing_status == "success":
                successful_files += 1
                total_vars += len(file_stats.variables)
        
        file_statistics.append(file_stats)
    
    summary = {
        "total_files": len(request.file_paths),
        "successful_files": successful_files,
        "failed_files": len(request.file_paths) - successful_files,
        "total_variables_analyzed": total_vars
    }
    
    return AnalysisResponse(
        file_statistics=file_statistics,
        summary=summary
    )

@router.post("/map-data", response_model=MapDataResponse)
async def get_map_data(request: AnalysisRequest):
    """Get location data for mapping visualizations"""
    
    locations = []
    unique_paths = list(set(request.file_paths))
    
    for file_path in unique_paths:
        if os.path.exists(file_path):
            # Unblock event loop
            file_stats = await asyncio.to_thread(read_netcdf_data, file_path)
            if (file_stats.latitude is not None and 
                file_stats.longitude is not None and
                not np.isnan(file_stats.latitude) and 
                not np.isnan(file_stats.longitude)):
                
                locations.append(LocationPoint(
                    latitude=file_stats.latitude,
                    longitude=file_stats.longitude,
                    file_path=file_path,
                    file_name=os.path.basename(file_path)
                ))
    
    center_lat = None
    center_lon = None
    if locations:
        center_lat = np.mean([loc.latitude for loc in locations])
        center_lon = np.mean([loc.longitude for loc in locations])
    
    return MapDataResponse(
        locations=locations,
        center_lat=center_lat,
        center_lon=center_lon
    )

@router.post("/insights", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest):
    """Generate AI insights from analyzed data"""
    
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Groq API key not configured. Cannot generate AI insights."
        )
    
    # Build compact, efficient context from file statistics
    successful_files = [f for f in request.file_statistics if f.processing_status == "success"]
    
    # Group data by geographic regions for more efficient summarization
    equatorial_data = []  # -10 to 10 degrees
    northern_data = []    # > 10 degrees  
    southern_data = []    # < -10 degrees
    locations = []
    
    all_temps = []
    all_salinity = []
    
    for file_stats in successful_files:
        if file_stats.latitude and file_stats.longitude:
            lat, lon = file_stats.latitude, file_stats.longitude
            locations.append(f"{lat:.1f}°N, {lon:.1f}°E")
            
            # Categorize by latitude
            if -10 <= lat <= 10:
                region_category = "equatorial"
                equatorial_data.append((lat, lon))
            elif lat > 10:
                region_category = "northern"
                northern_data.append((lat, lon))
            else:
                region_category = "southern"
                southern_data.append((lat, lon))
            
            # Collect temperature and salinity ranges (only main variables, not errors/QC)
            for var in file_stats.variables:
                if var.variable_name in ['TEMP', 'TEMP_ADJUSTED']:
                    all_temps.extend([var.min_value, var.max_value])
                elif var.variable_name in ['PSAL', 'PSAL_ADJUSTED']:
                    all_salinity.extend([var.min_value, var.max_value])
    
    # Create compact regional summary
    regional_summary = []
    if equatorial_data:
        regional_summary.append(f"{len(equatorial_data)} equatorial profiles")
    if northern_data:
        regional_summary.append(f"{len(northern_data)} northern hemisphere profiles")
    if southern_data:
        regional_summary.append(f"{len(southern_data)} southern hemisphere profiles")
    
    # Compute overall ranges
    temp_summary = ""
    if all_temps:
        temp_min, temp_max = min(all_temps), max(all_temps)
        temp_summary = f"Temperature range: {temp_min:.1f} to {temp_max:.1f}°C. "
    
    salinity_summary = ""
    if all_salinity:
        sal_min, sal_max = min(all_salinity), max(all_salinity)
        salinity_summary = f"Salinity range: {sal_min:.1f} to {sal_max:.1f} psu. "
    
    # Create natural but compact data summary
    data_summary = f"I've analyzed {len(successful_files)} ocean profiles from {', '.join(regional_summary)}. {temp_summary}{salinity_summary}"
    if len(locations) <= 5:
        data_summary += f"Specific locations: {', '.join(locations)}."
    else:
        data_summary += f"Locations include {', '.join(locations[:3])} and {len(locations)-3} others."
    
    prompt = (
        f"You are an experienced oceanographer analyzing real ocean data. Write a natural, conversational response to: '{request.query}'\\n\\n"
        f"Data overview: {data_summary}\\n\\n"
        f"Instructions:\\n"
        f"- Write like you're explaining to a colleague, not a formal report\\n"
        f"- Use natural language, not bullet points or structured lists\\n"
        f"- Focus on the most interesting oceanographic patterns\\n"
        f"- Only mention data quality issues if they're significant\\n"
        f"- Keep it conversational and engaging, around 2-3 paragraphs\\n"
        f"- Don't repeat the same information multiple times\\n"
        f"- Sound like a real scientist discussing their findings\\n\\n"
        f"Remember: Ocean temps typically range -2 to 35°C, salinity 30-40 psu. "
        f"Be authentic and avoid robotic language."
    )
    
    try:
        # Unblock event loop during synchronous HTTP request
        response = await asyncio.to_thread(
            requests.post,
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a friendly, conversational oceanographer with deep expertise. Speak naturally like you're discussing fascinating ocean data with a colleague. Vary your response style - sometimes excited about discoveries, sometimes thoughtful about patterns, always authentic."},
                    {"role": "assistant", "content": "Here's an example of how I'd naturally discuss ocean data: 'Looking at these profiles from the Arabian Sea, what's really striking is how the salinity signature changes as you move closer to the coast. You can clearly see the influence of monsoon-driven mixing in the upper waters, and that classic intermediate water mass around 800m depth that we always see in this region.'"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            insights = response.json()["choices"][0]["message"]["content"].strip()
        else:
            insights = f"❌ Groq API Error {response.status_code}: {response.text}"
    
    except requests.exceptions.Timeout:
        insights = "❌ Request timeout while generating insights. Please try again."
    except Exception as e:
        insights = f"❌ API call failed: {str(e)}"
    
    return InsightsResponse(
        insights=insights,
        query=request.query,
        files_analyzed=len([f for f in request.file_statistics if f.processing_status == "success"])
    )
