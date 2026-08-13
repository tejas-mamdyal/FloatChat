import Plot from 'react-plotly.js';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { TrendingUp, BarChart3, Activity, Globe } from 'lucide-react';

const PlotlyCharts = ({ analysisData }) => {
  // Generate sample charts when no analysis data is available - Temperature, Pressure, and Salinity only
  const generateSampleCharts = () => {
    const sampleTemperatureData = {
      x: [0, 50, 100, 200, 500, 1000, 1500, 2000],
      y: [24.5, 22.1, 18.7, 15.2, 8.9, 4.2, 2.1, 1.8],
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Temperature',
      line: { color: '#ef4444', width: 3 },
      marker: { size: 8 }
    };

    const sampleSalinityData = {
      x: [0, 50, 100, 200, 500, 1000, 1500, 2000],
      y: [35.1, 35.3, 35.0, 34.8, 34.5, 34.7, 34.9, 34.95],
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Salinity',
      line: { color: '#3b82f6', width: 3 },
      marker: { size: 8 }
    };

    const samplePressureData = {
      x: [0, 50, 100, 200, 500, 1000, 1500, 2000],
      y: [0, 0.5, 1.0, 2.0, 5.1, 10.1, 15.2, 20.3],
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Pressure',
      line: { color: '#10b981', width: 3 },
      marker: { size: 8 }
    };

    return {
      temperature: sampleTemperatureData,
      salinity: sampleSalinityData,
      pressure: samplePressureData
    };
  };

  // Generate charts from analysis data - filtered for Temperature, Pressure, and Salinity only
  const generateAnalysisCharts = () => {
    if (!analysisData || !analysisData.file_statistics) return null;

    const charts = [];
    const allowedVariables = ['temperature', 'pressure', 'salinity', 'temp', 'pres', 'sal', 'TEMP', 'PRES', 'SAL', 'Temperature', 'Pressure', 'Salinity'];
    
    // Helper function to check if a variable should be included
    const isAllowedVariable = (varName) => {
      return allowedVariables.some(allowed => 
        varName.toLowerCase().includes(allowed.toLowerCase())
      );
    };
    
    // Process file statistics to create meaningful charts
    analysisData.file_statistics.forEach((fileStats, fileIndex) => {
      if (fileStats.variables && fileStats.variables.length > 0) {
        // Filter variables to only include Temperature, Pressure, and Salinity
        const filteredVariables = fileStats.variables.filter(v => isAllowedVariable(v.variable_name));
        
        if (filteredVariables.length > 0) {
          // Variable values chart
          const variableNames = filteredVariables.map(v => v.variable_name);
          const meanValues = filteredVariables.map(v => v.mean_value);
          
          charts.push({
            id: `variables_${fileIndex}`,
            title: `Ocean Parameters in ${fileStats.file_path.split('/').pop()}`,
            data: [{
              x: variableNames,
              y: meanValues,
              type: 'bar',
              marker: { 
                color: meanValues.map((_, i) => {
                  const varName = variableNames[i].toLowerCase();
                  if (varName.includes('temp')) return '#ef4444'; // Red for temperature
                  if (varName.includes('pres')) return '#10b981'; // Green for pressure
                  if (varName.includes('sal')) return '#3b82f6';  // Blue for salinity
                  return '#6b7280'; // Gray fallback
                })
              }
            }],
            layout: {
              xaxis: { title: 'Ocean Parameters' },
              yaxis: { title: 'Mean Values' },
              height: 400
            }
          });

          // Min/Max range chart for each variable
          if (filteredVariables.length > 1) {
            const minValues = filteredVariables.map(v => v.min_value);
            const maxValues = filteredVariables.map(v => v.max_value);
            
            charts.push({
              id: `ranges_${fileIndex}`,
              title: `Value Ranges - ${fileStats.file_path.split('/').pop()}`,
              data: [
                {
                  x: variableNames,
                  y: minValues,
                  type: 'bar',
                  name: 'Min Values',
                  marker: { color: '#3b82f6' }
                },
                {
                  x: variableNames,
                  y: maxValues,
                  type: 'bar',
                  name: 'Max Values',
                  marker: { color: '#ef4444' }
                }
              ],
              layout: {
                xaxis: { title: 'Ocean Parameters' },
                yaxis: { title: 'Values' },
                barmode: 'group',
                height: 400
              }
            });
          }
        }
      }
    });

    return charts;
  };

  const sampleCharts = generateSampleCharts();
  const analysisCharts = generateAnalysisCharts();

  const commonLayout = {
    font: { family: 'Inter, sans-serif' },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 40, r: 40, b: 60, l: 60 }
  };

  return (
    <div className="space-y-6">
      {/* Analysis Data Charts */}
      {analysisCharts && analysisCharts.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold">Analysis Results</h3>
            <Badge variant="default">{analysisCharts.length} charts</Badge>
          </div>
          
          {analysisCharts.map((chart) => (
            <Card key={chart.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  {chart.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Plot
                  data={chart.data}
                  layout={{
                    ...commonLayout,
                    ...chart.layout,
                    title: undefined
                  }}
                  config={{ responsive: true }}
                  style={{ width: '100%' }}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Sample/Demo Charts */}
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-green-600" />
          <h3 className="text-lg font-semibold">Ocean Data Visualizations</h3>
          <Badge variant="outline">Demo Charts</Badge>
        </div>

        {/* Temperature Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-red-500" />
              Ocean Temperature Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Plot
              data={[sampleCharts.temperature]}
              layout={{
                ...commonLayout,
                title: undefined,
                xaxis: { title: 'Depth (m)', autorange: 'reversed' },
                yaxis: { title: 'Temperature (°C)' },
                height: 400
              }}
              config={{ responsive: true }}
              style={{ width: '100%' }}
            />
          </CardContent>
        </Card>

        {/* Salinity Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-500" />
              Ocean Salinity Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Plot
              data={[sampleCharts.salinity]}
              layout={{
                ...commonLayout,
                title: undefined,
                xaxis: { title: 'Depth (m)', autorange: 'reversed' },
                yaxis: { title: 'Salinity (PSU)' },
                height: 400
              }}
              config={{ responsive: true }}
              style={{ width: '100%' }}
            />
          </CardContent>
        </Card>

        {/* Pressure Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-green-500" />
              Ocean Pressure Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Plot
              data={[sampleCharts.pressure]}
              layout={{
                ...commonLayout,
                title: undefined,
                xaxis: { title: 'Depth (m)', autorange: 'reversed' },
                yaxis: { title: 'Pressure (MPa)' },
                height: 400
              }}
              config={{ responsive: true }}
              style={{ width: '100%' }}
            />
          </CardContent>
        </Card>
      </div>

      {/* Info Alert */}
      <Alert>
        <Activity className="h-4 w-4" />
        <AlertDescription>
          {analysisCharts && analysisCharts.length > 0 
            ? "Charts above show real analysis results from your queries. The sample charts below demonstrate typical ocean data visualizations."
            : "Use the AI Chat to query ocean data and see real analysis results here. The charts above show sample ocean data visualizations."
          }
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default PlotlyCharts;
