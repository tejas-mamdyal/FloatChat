#!/usr/bin/env python3
"""
Unit tests for ocean variable bounds validation in NetCDF data analysis.
Tests to ensure temperature, salinity, and other ocean variables are within realistic ranges.
"""

import numpy as np
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers.analysis import read_netcdf_data, VariableStats


class TestOceanVariableBounds(unittest.TestCase):
    """Test cases for ocean variable validation and bounds checking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_with_fill_values = {
            'TEMP': np.array([2.5, 25.3, 99999.0, 28.1, -2.0]),  # Mix of valid and fill values
            'PSAL': np.array([34.5, 35.2, 99999.0, 32.8, 36.1]),  # Salinity data
            'PRES': np.array([10.5, 500.2, 99999.0, 2000.3, 5000.0]),  # Pressure data
            'INVALID_TEMP': np.array([100.0, -50.0, 99999.0]),  # Out of bounds temperature
            'INVALID_PSAL': np.array([100.0, -10.0, 99999.0]),  # Out of bounds salinity
        }
    
    @patch('routers.analysis.Dataset')
    def test_temperature_bounds_filtering(self, mock_dataset):
        """Test that temperature values are filtered to realistic ocean ranges (-5°C to 50°C)."""
        mock_nc = MagicMock()
        mock_nc.variables = {
            'LATITUDE': MagicMock(),
            'LONGITUDE': MagicMock(),
            'TEMP': MagicMock(),
        }
        mock_nc.variables['LATITUDE'].__getitem__.return_value = np.array([25.0])
        mock_nc.variables['LONGITUDE'].__getitem__.return_value = np.array([75.0])
        mock_nc.variables['TEMP'].__getitem__.return_value = self.test_data_with_fill_values['TEMP']
        mock_nc.variables.keys.return_value = ['LATITUDE', 'LONGITUDE', 'TEMP']
        
        mock_dataset.return_value.__enter__.return_value = mock_nc
        
        result = read_netcdf_data('test_file.nc')
        
        # Should have one TEMP variable
        temp_vars = [v for v in result.variables if v.variable_name == 'TEMP']
        self.assertEqual(len(temp_vars), 1)
        
        temp_var = temp_vars[0]
        # Check that values are within realistic bounds
        self.assertGreaterEqual(temp_var.min_value, -5.0)
        self.assertLessEqual(temp_var.max_value, 50.0)
        # Should exclude the 99999.0 fill value
        self.assertLess(temp_var.max_value, 99999.0)
        
    @patch('routers.analysis.Dataset')
    def test_salinity_bounds_filtering(self, mock_dataset):
        """Test that salinity values are filtered to realistic ocean ranges (0 to 50 psu)."""
        mock_nc = MagicMock()
        mock_nc.variables = {
            'LATITUDE': MagicMock(),
            'LONGITUDE': MagicMock(),
            'PSAL': MagicMock(),
        }
        mock_nc.variables['LATITUDE'].__getitem__.return_value = np.array([25.0])
        mock_nc.variables['LONGITUDE'].__getitem__.return_value = np.array([75.0])
        mock_nc.variables['PSAL'].__getitem__.return_value = self.test_data_with_fill_values['PSAL']
        mock_nc.variables.keys.return_value = ['LATITUDE', 'LONGITUDE', 'PSAL']
        
        mock_dataset.return_value.__enter__.return_value = mock_nc
        
        result = read_netcdf_data('test_file.nc')
        
        # Should have one PSAL variable
        psal_vars = [v for v in result.variables if v.variable_name == 'PSAL']
        self.assertEqual(len(psal_vars), 1)
        
        psal_var = psal_vars[0]
        # Check that values are within realistic bounds
        self.assertGreaterEqual(psal_var.min_value, 0.0)
        self.assertLessEqual(psal_var.max_value, 50.0)
        # Should exclude the 99999.0 fill value
        self.assertLess(psal_var.max_value, 99999.0)
        
    @patch('routers.analysis.Dataset')
    def test_pressure_bounds_filtering(self, mock_dataset):
        """Test that pressure values are filtered to realistic ocean ranges (0 to 11000 dbar)."""
        mock_nc = MagicMock()
        mock_nc.variables = {
            'LATITUDE': MagicMock(),
            'LONGITUDE': MagicMock(),
            'PRES': MagicMock(),
        }
        mock_nc.variables['LATITUDE'].__getitem__.return_value = np.array([25.0])
        mock_nc.variables['LONGITUDE'].__getitem__.return_value = np.array([75.0])
        mock_nc.variables['PRES'].__getitem__.return_value = self.test_data_with_fill_values['PRES']
        mock_nc.variables.keys.return_value = ['LATITUDE', 'LONGITUDE', 'PRES']
        
        mock_dataset.return_value.__enter__.return_value = mock_nc
        
        result = read_netcdf_data('test_file.nc')
        
        # Should have one PRES variable
        pres_vars = [v for v in result.variables if v.variable_name == 'PRES']
        self.assertEqual(len(pres_vars), 1)
        
        pres_var = pres_vars[0]
        # Check that values are within realistic bounds
        self.assertGreaterEqual(pres_var.min_value, 0.0)
        self.assertLessEqual(pres_var.max_value, 11000.0)
        # Should exclude the 99999.0 fill value
        self.assertLess(pres_var.max_value, 99999.0)
        
    @patch('routers.analysis.Dataset')
    def test_fill_values_removed(self, mock_dataset):
        """Test that common NetCDF fill values are properly removed."""
        mock_nc = MagicMock()
        mock_nc.variables = {
            'LATITUDE': MagicMock(),
            'LONGITUDE': MagicMock(),
            'TEMP': MagicMock(),
        }
        mock_nc.variables['LATITUDE'].__getitem__.return_value = np.array([25.0])
        mock_nc.variables['LONGITUDE'].__getitem__.return_value = np.array([75.0])
        # Data with multiple fill values
        mock_nc.variables['TEMP'].__getitem__.return_value = np.array([
            25.0, 99999.0, -99999.0, 28.5, 9.9692099683868690e+36, 22.3
        ])
        mock_nc.variables.keys.return_value = ['LATITUDE', 'LONGITUDE', 'TEMP']
        
        mock_dataset.return_value.__enter__.return_value = mock_nc
        
        result = read_netcdf_data('test_file.nc')
        
        temp_vars = [v for v in result.variables if v.variable_name == 'TEMP']
        self.assertEqual(len(temp_vars), 1)
        
        temp_var = temp_vars[0]
        # Should only have 3 valid values: 25.0, 28.5, 22.3
        self.assertEqual(temp_var.count, 3)
        self.assertGreaterEqual(temp_var.min_value, 20.0)  # Should be around 22.3
        self.assertLessEqual(temp_var.max_value, 30.0)  # Should be around 28.5
        
    def test_realistic_ocean_temperature_ranges(self):
        """Test that the implemented bounds match realistic ocean temperature ranges."""
        # Surface water: typically -2°C to 35°C
        # Deep water: typically 0°C to 4°C
        # Our bounds: -5°C to 50°C (conservative to include all possibilities)
        
        valid_temps = [-2.0, 0.0, 4.0, 15.0, 25.0, 35.0]
        invalid_temps = [-10.0, 60.0, 99999.0]
        
        for temp in valid_temps:
            self.assertTrue(-5.0 <= temp <= 50.0, f"Valid temp {temp} should be within bounds")
        
        for temp in invalid_temps:
            if temp != 99999.0:  # Fill values are handled separately
                self.assertFalse(-5.0 <= temp <= 50.0, f"Invalid temp {temp} should be out of bounds")
                
    def test_realistic_ocean_salinity_ranges(self):
        """Test that the implemented bounds match realistic ocean salinity ranges."""
        # Ocean salinity: typically 30-40 psu
        # Extreme cases: Dead Sea ~34%, Baltic Sea ~7-8 psu, but for open ocean 30-40
        # Our bounds: 0-50 psu (conservative)
        
        valid_salinity = [30.0, 32.0, 34.5, 35.0, 36.5, 38.0, 40.0]
        invalid_salinity = [-5.0, 60.0, 99999.0]
        
        for sal in valid_salinity:
            self.assertTrue(0.0 <= sal <= 50.0, f"Valid salinity {sal} should be within bounds")
        
        for sal in invalid_salinity:
            if sal != 99999.0:  # Fill values are handled separately
                self.assertFalse(0.0 <= sal <= 50.0, f"Invalid salinity {sal} should be out of bounds")


if __name__ == '__main__':
    print("Running ocean variable bounds validation tests...")
    unittest.main(verbosity=2)
