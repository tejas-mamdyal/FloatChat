import { useState, useEffect } from "react";
import { 
  BarChart3, 
  Map, 
  Settings, 
  TrendingUp, 
  Waves, 
  MessageSquare, 
  Send,
  Menu,
  X,
  Thermometer,
  Droplets,
  Globe,
  Calendar,
  Download,
  Share,
  LogOut,
  Loader2,
  AlertCircle,
  CheckCircle
} from "lucide-react";
import MapComponent from "@/components/MapComponent";
import PlotlyCharts from "@/components/PlotlyCharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@/hooks/useAuth.jsx";
import { toast } from "sonner";
import apiService from "@/services/api";
import argoFloatImage from '@/assets/argo-float.jpg';
import oceanProfilesImage from '@/assets/ocean-profiles.jpg';
import oceanSensorsImage from '@/assets/ocean-sensors.jpg';
import argoGlobalMapImage from '@/assets/argo-global-map.jpg';

const FloatChatAppEnhanced = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("chat");
  const [chatMessage, setChatMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [insights, setInsights] = useState(null);
  const { user, signOut } = useAuth();

  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "system",
      content: "Welcome to FloatChat! I can help you explore ARGO ocean data. Try asking: 'Show me temperature profiles near the equator' or 'Find salinity data in the Arabian Sea'"
    }
  ]);

  // Check system health on component mount
  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const health = await apiService.checkHealth();
      setSystemHealth(health);
      if (health.status === "degraded") {
        toast.warning("System is running with limited functionality");
      }
    } catch (error) {
      setSystemHealth({ status: "error", message: error.message });
      toast.error("Unable to connect to backend system");
    }
  };

  const handleLogout = async () => {
    const { error } = await signOut();
    if (error) {
      toast.error("Failed to sign out");
    } else {
      toast.success("Successfully signed out");
    }
  };

  const sidebarItems = [
    { id: "chat", label: "AI Chat", icon: MessageSquare },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "map", label: "Map View", icon: Map },
    { id: "ndvi", label: "NDVI Analysis", icon: TrendingUp },
    { id: "profiles", label: "Ocean Profiles", icon: Waves },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  const handleSendMessage = async () => {
    if (!chatMessage.trim() || loading) return;
    
    const userMessage = chatMessage;
    
    // Add user message immediately
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: "user",
      content: userMessage
    }]);
    
    setChatMessage("");
    setLoading(true);

    try {
      // Add loading message
      const loadingId = Date.now() + 1;
      setMessages(prev => [...prev, {
        id: loadingId,
        type: "assistant",
        content: "Searching ocean data and analyzing results...",
        loading: true
      }]);

      // Call the integrated search and analyze API
      const result = await apiService.searchAndAnalyze(userMessage, 20);
      
      // Remove loading message
      setMessages(prev => prev.filter(msg => msg.id !== loadingId));

      if (result.error) {
        setMessages(prev => [...prev, {
          id: Date.now() + 2,
          type: "assistant",
          content: `I encountered an error: ${result.error}. Please try rephrasing your query or check if the backend system is running.`
        }]);
      } else {
        // Store results for other tabs
        setSearchResults(result.searchResults);
        setAnalysisData(result.analysis);
        setMapData(result.mapData);
        setInsights(result.insights);

        // Create response message
        let responseContent = `Found ${result.searchResults.total_found} relevant files for your query.\n\n`;
        
        if (result.analysis && result.analysis.summary) {
          responseContent += `📊 **Analysis Summary:**\n`;
          responseContent += `- Files analyzed: ${result.analysis.summary.successful_files}/${result.analysis.summary.total_files}\n`;
          responseContent += `- Variables analyzed: ${result.analysis.summary.total_variables_analyzed}\n\n`;
        }

        if (result.mapData && result.mapData.locations.length > 0) {
          responseContent += `🗺️ **Location Data:** Found ${result.mapData.locations.length} locations with valid coordinates\n\n`;
        }

        if (result.insights && result.insights.insights) {
          responseContent += `🤖 **AI Insights:**\n${result.insights.insights}`;
        }

        setMessages(prev => [...prev, {
          id: Date.now() + 3,
          type: "assistant",
          content: responseContent
        }]);

        // Switch to analytics tab to show results
        toast.success("Analysis complete! Check the Analytics and Map tabs for detailed results.");
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => !msg.loading));
      setMessages(prev => [...prev, {
        id: Date.now() + 4,
        type: "assistant",
        content: `I encountered an error while processing your request: ${error.message}. Please make sure the backend system is running and try again.`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuery = (query) => {
    setChatMessage(query);
  };

  const renderChatContent = () => (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.type === "user"
                  ? "bg-blue-600 text-white"
                  : message.type === "system"
                  ? "bg-green-100 text-green-800 border border-green-200"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {message.loading && (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>{message.content}</span>
                </div>
              )}
              {!message.loading && (
                <div className="whitespace-pre-line">{message.content}</div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            placeholder="Ask about ocean data..."
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
            disabled={loading}
          />
          <Button onClick={handleSendMessage} disabled={loading || !chatMessage.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          <Badge 
            variant="outline" 
            className="cursor-pointer text-xs hover:bg-gray-100"
            onClick={() => handleQuickQuery("Temperature profiles near the equator")}
          >
            Temperature profiles equator
          </Badge>
          <Badge 
            variant="outline" 
            className="cursor-pointer text-xs hover:bg-gray-100"
            onClick={() => handleQuickQuery("Salinity data in Arabian Sea")}
          >
            Salinity Arabian Sea
          </Badge>
          <Badge 
            variant="outline" 
            className="cursor-pointer text-xs hover:bg-gray-100"
            onClick={() => handleQuickQuery("Pressure profiles Pacific Ocean")}
          >
            Pressure profiles Pacific
          </Badge>
        </div>
        
        {/* System Status */}
        {systemHealth && (
          <div className="mt-3">
            <Alert>
              <div className="flex items-center gap-2">
                {systemHealth.status === "healthy" ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                <AlertDescription>
                  Backend: {systemHealth.status} • ChromaDB: {systemHealth.chroma_available ? "✓" : "✗"} • 
                  Config: {systemHealth.config_available ? "✓" : "✗"}
                </AlertDescription>
              </div>
            </Alert>
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalyticsContent = () => (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Ocean Data Analytics</h2>
        <div className="relative w-16 h-16 rounded-lg overflow-hidden">
          <img src={oceanSensorsImage} alt="Ocean Sensors" className="w-full h-full object-cover" />
        </div>
      </div>
      
      {/* Analysis Results */}
      {analysisData && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Latest Analysis Results</h3>
          
          {/* Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <Globe className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                <div className="text-2xl font-bold">{analysisData.summary.successful_files}</div>
                <div className="text-sm text-muted-foreground">Files Analyzed</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <BarChart3 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                <div className="text-2xl font-bold">{analysisData.summary.total_variables_analyzed}</div>
                <div className="text-sm text-muted-foreground">Variables</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <Map className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                <div className="text-2xl font-bold">{mapData?.locations.length || 0}</div>
                <div className="text-sm text-muted-foreground">Locations</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-cyan-500" />
                <div className="text-2xl font-bold">{searchResults?.search_method || "N/A"}</div>
                <div className="text-sm text-muted-foreground">Search Method</div>
              </CardContent>
            </Card>
          </div>

          {/* File Statistics */}
          <div className="space-y-4">
            <h4 className="font-semibold">File Statistics ({analysisData.file_statistics.length} files)</h4>
            <div className="max-h-[600px] overflow-y-auto space-y-4">
            {analysisData.file_statistics.map((fileStats, index) => {
              // Categorize variables into Core Ocean and BGC parameters
              const coreVariables = fileStats.variables.filter(variable => {
                const varName = variable.variable_name.toLowerCase();
                return varName.includes('temp') || varName.includes('pres') || varName.includes('sal');
              });
              
              const bgcVariables = fileStats.variables.filter(variable => {
                const varName = variable.variable_name.toLowerCase();
                return varName.includes('chl') || varName.includes('chlorophyll') ||
                       varName.includes('doxy') || varName.includes('oxygen') || varName.includes('o2') ||
                       varName.includes('no3') || varName.includes('nitrate') ||
                       varName.includes('ph');
              });
              
              return (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="text-base">
                      {fileStats.file_path.split('/').pop() || fileStats.file_path}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                      <div>
                        <span className="font-medium">Status:</span> {fileStats.processing_status}
                      </div>
                      {fileStats.latitude && (
                        <div>
                          <span className="font-medium">Lat:</span> {fileStats.latitude.toFixed(2)}°
                        </div>
                      )}
                      {fileStats.longitude && (
                        <div>
                          <span className="font-medium">Lon:</span> {fileStats.longitude.toFixed(2)}°
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Total Variables:</span> {fileStats.variables.length}
                      </div>
                    </div>
                    
                    {/* Variable Type Breakdown */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {coreVariables.length > 0 && (
                        <div>
                          <h5 className="font-medium text-sm mb-2 text-blue-700">Core Ocean ({coreVariables.length})</h5>
                          <div className="flex flex-wrap gap-1">
                            {coreVariables.map((variable, vIndex) => (
                              <span key={vIndex} className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                                {variable.variable_name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {bgcVariables.length > 0 && (
                        <div>
                          <h5 className="font-medium text-sm mb-2 text-emerald-700">BGC Parameters ({bgcVariables.length})</h5>
                          <div className="flex flex-wrap gap-1">
                            {bgcVariables.map((variable, vIndex) => (
                              <span key={vIndex} className="inline-flex items-center px-2 py-1 rounded text-xs bg-emerald-100 text-emerald-800">
                                {variable.variable_name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            </div>
          </div>
          
          {/* Interactive Charts */}
          <PlotlyCharts analysisData={analysisData} />
        </div>
      )}

          {/* Default Analytics Display */}
          {!analysisData && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardContent className="p-4 text-center">
                    <Thermometer className="h-8 w-8 mx-auto mb-2 text-red-500" />
                    <div className="text-2xl font-bold">24.5°C</div>
                    <div className="text-sm text-muted-foreground">Avg Temperature</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <Droplets className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                    <div className="text-2xl font-bold">34.7</div>
                    <div className="text-sm text-muted-foreground">Avg Salinity</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <Waves className="h-8 w-8 mx-auto mb-2 text-cyan-500" />
                    <div className="text-2xl font-bold">1,234</div>
                    <div className="text-sm text-muted-foreground">Active Floats</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <Globe className="h-8 w-8 mx-auto mb-2 text-green-500" />
                    <div className="text-2xl font-bold">456</div>
                    <div className="text-sm text-muted-foreground">New Profiles</div>
                  </CardContent>
                </Card>
              </div>

              {/* BGC Parameters Section */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4 text-emerald-700">Biogeochemical (BGC) Parameters</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="h-8 w-8 mx-auto mb-2 bg-emerald-100 rounded-full flex items-center justify-center">
                        <span className="text-emerald-600 font-bold text-sm">Chl</span>
                      </div>
                      <div className="text-2xl font-bold text-emerald-600">0.8</div>
                      <div className="text-sm text-muted-foreground">Chlorophyll (mg/m³)</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="h-8 w-8 mx-auto mb-2 bg-sky-100 rounded-full flex items-center justify-center">
                        <span className="text-sky-600 font-bold text-sm">O₂</span>
                      </div>
                      <div className="text-2xl font-bold text-sky-600">245</div>
                      <div className="text-sm text-muted-foreground">Oxygen (μmol/kg)</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="h-8 w-8 mx-auto mb-2 bg-amber-100 rounded-full flex items-center justify-center">
                        <span className="text-amber-600 font-bold text-sm">NO₃</span>
                      </div>
                      <div className="text-2xl font-bold text-amber-600">15.2</div>
                      <div className="text-sm text-muted-foreground">Nitrate (μmol/kg)</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="h-8 w-8 mx-auto mb-2 bg-purple-100 rounded-full flex items-center justify-center">
                        <span className="text-purple-600 font-bold text-sm">pH</span>
                      </div>
                      <div className="text-2xl font-bold text-purple-600">8.1</div>
                      <div className="text-sm text-muted-foreground">pH Level</div>
                    </CardContent>
                  </Card>
                </div>
              </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>ARGO Float Network</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative h-48 rounded-lg overflow-hidden">
                  <img src={argoFloatImage} alt="ARGO Float" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
                    <div className="p-4 text-white">
                      <p className="text-sm font-medium">Autonomous Profiling Floats</p>
                      <p className="text-xs opacity-90">Real-time ocean monitoring</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Ocean Profile Data</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative h-48 rounded-lg overflow-hidden">
                  <img src={oceanProfilesImage} alt="Ocean Profiles" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
                    <div className="p-4 text-white">
                      <p className="text-sm font-medium">Temperature & Salinity Profiles</p>
                      <p className="text-xs opacity-90">Depth-based measurements</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              To see real analysis results, use the AI Chat to query ocean data. The system will analyze and display results here.
            </AlertDescription>
          </Alert>
          
          {/* Add Plotly Charts */}
          <PlotlyCharts analysisData={analysisData} />
        </>
      )}
    </div>
  );

  const renderMapContent = () => (
    <div className="h-full overflow-y-auto p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Global Ocean Map</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Share className="h-4 w-4 mr-1" />
            Share
          </Button>
        </div>
      </div>

      {/* Map Data Results Alert */}
      {mapData && mapData.locations.length > 0 && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Found {mapData.locations.length} locations with valid coordinates. 
            Center: {mapData.center_lat?.toFixed(2)}°N, {mapData.center_lon?.toFixed(2)}°E
          </AlertDescription>
        </Alert>
      )}

      {/* Interactive Leaflet Map */}
      <MapComponent mapData={mapData} height="500px" />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {mapData ? `${mapData.locations.length}` : "Indian Ocean"}
            </div>
            <div className="text-sm text-muted-foreground">
              {mapData ? "Data Points" : "Primary Focus Region"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">Real-time</div>
            <div className="text-sm text-muted-foreground">Data Updates</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">Multi-layer</div>
            <div className="text-sm text-muted-foreground">Visualization</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case "chat":
        return renderChatContent();
      case "analytics":
        return renderAnalyticsContent();
      case "map":
        return renderMapContent();
      case "ndvi":
        return (
          <div className="h-full overflow-y-auto p-6">
            <h2 className="text-2xl font-bold mb-4">NDVI Analysis</h2>
            {insights && (
              <Card className="mb-4">
                <CardHeader>
                  <CardTitle>AI Insights from Latest Query</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="whitespace-pre-line text-sm">{insights.insights}</div>
                </CardContent>
              </Card>
            )}
            <Card>
              <CardContent className="p-8 text-center">
                <TrendingUp className="h-16 w-16 mx-auto mb-4 text-green-500" />
                <h3 className="text-xl font-semibold mb-2">Vegetation Index Correlation</h3>
                <p className="text-muted-foreground">
                  Analyze correlations between ocean parameters and vegetation indices
                </p>
              </CardContent>
            </Card>
          </div>
        );
      case "profiles":
        return (
          <div className="h-full overflow-y-auto p-6 space-y-6">
            <h2 className="text-2xl font-bold mb-4">Ocean Profiles</h2>
            
            {/* Show analysis data if available - filtered for Core Ocean and BGC Parameters */}
            {analysisData && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Ocean Parameters Analysis (Core + BGC Parameters)</h3>
                <div className="max-h-[500px] overflow-y-auto space-y-4">
                {analysisData.file_statistics.map((fileStats, index) => {
                  // Filter variables to include Core Ocean Parameters + BGC Parameters
                  const allowedVariables = [
                    // Core Ocean Parameters
                    'temperature', 'pressure', 'salinity', 'temp', 'pres', 'sal', 'TEMP', 'PRES', 'SAL', 'Temperature', 'Pressure', 'Salinity',
                    // BGC Parameters
                    'chlorophyll', 'chl', 'CHL', 'Chlorophyll', 'CHLA', 'chla',
                    'oxygen', 'doxy', 'DOXY', 'Oxygen', 'OXYGEN', 'o2', 'O2',
                    'nitrate', 'no3', 'NO3', 'Nitrate', 'NITRATE',
                    'ph', 'pH', 'PH', 'Ph'
                  ];
                  const filteredVariables = fileStats.variables.filter(variable => 
                    allowedVariables.some(allowed => 
                      variable.variable_name.toLowerCase().includes(allowed.toLowerCase())
                    )
                  );
                  
                  return filteredVariables.length > 0 && (
                    <Card key={index}>
                      <CardHeader>
                        <CardTitle className="text-base">
                          {fileStats.file_path.split('/').pop()} ({filteredVariables.length} ocean parameters)
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {filteredVariables.map((variable, vIndex) => {
                            const varName = variable.variable_name.toLowerCase();
                            const getVariableColor = () => {
                              // Core Ocean Parameters
                              if (varName.includes('temp')) return 'bg-red-50 border-red-200';
                              if (varName.includes('pres')) return 'bg-green-50 border-green-200';
                              if (varName.includes('sal')) return 'bg-blue-50 border-blue-200';
                              // BGC Parameters
                              if (varName.includes('chl') || varName.includes('chlorophyll')) return 'bg-emerald-50 border-emerald-200';
                              if (varName.includes('doxy') || varName.includes('oxygen') || varName.includes('o2')) return 'bg-sky-50 border-sky-200';
                              if (varName.includes('no3') || varName.includes('nitrate')) return 'bg-amber-50 border-amber-200';
                              if (varName.includes('ph')) return 'bg-purple-50 border-purple-200';
                              return 'bg-gray-50 border-gray-200';
                            };
                            
                            const getVariableIcon = () => {
                              if (varName.includes('chl') || varName.includes('chlorophyll')) return 'Chl';
                              if (varName.includes('doxy') || varName.includes('oxygen') || varName.includes('o2')) return 'O₂';
                              if (varName.includes('no3') || varName.includes('nitrate')) return 'NO₃';
                              if (varName.includes('ph')) return 'pH';
                              if (varName.includes('temp')) return 'T';
                              if (varName.includes('pres')) return 'P';
                              if (varName.includes('sal')) return 'S';
                              return '?';
                            };
                            
                            return (
                              <div key={vIndex} className={`p-3 rounded border ${getVariableColor()}`}>
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-xs bg-white rounded px-1 py-0.5 font-bold">
                                    {getVariableIcon()}
                                  </span>
                                  <div className="font-medium text-sm truncate">{variable.variable_name}</div>
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  <div>Mean: {variable.mean_value.toFixed(3)}</div>
                                  <div>Range: {variable.min_value.toFixed(3)} - {variable.max_value.toFixed(3)}</div>
                                  <div>Trend: {variable.trend}</div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Profile Visualization</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative h-64 rounded-lg overflow-hidden">
                    <img src={oceanProfilesImage} alt="Ocean Temperature Profiles" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
                      <div className="p-4 text-white">
                        <p className="text-sm font-medium">Temperature & Salinity by Depth</p>
                        <p className="text-xs opacity-90">Interactive depth profiles</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>ARGO Float Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative h-64 rounded-lg overflow-hidden">
                    <img src={argoFloatImage} alt="ARGO Float Equipment" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
                      <div className="p-4 text-white">
                        <p className="text-sm font-medium">Autonomous Ocean Monitoring</p>
                        <p className="text-xs opacity-90">Global fleet of 4,000+ floats</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* Core Ocean Parameters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-xl font-bold text-red-500">Temperature</div>
                  <div className="text-sm text-muted-foreground">°C Profile</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-xl font-bold text-blue-500">Salinity</div>
                  <div className="text-sm text-muted-foreground">PSU Profile</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-xl font-bold text-green-500">Pressure</div>
                  <div className="text-sm text-muted-foreground">MPa Profile</div>
                </CardContent>
              </Card>
            </div>

            {/* BGC Parameters */}
            <div className="mb-4">
              <h4 className="text-lg font-semibold mb-4 text-emerald-700">Biogeochemical (BGC) Parameters</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-xl font-bold text-emerald-600">Chlorophyll</div>
                    <div className="text-sm text-muted-foreground">mg/m³ Profile</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-xl font-bold text-sky-600">Oxygen</div>
                    <div className="text-sm text-muted-foreground">μmol/kg Profile</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-xl font-bold text-amber-600">Nitrate</div>
                    <div className="text-sm text-muted-foreground">μmol/kg Profile</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-xl font-bold text-purple-600">pH</div>
                    <div className="text-sm text-muted-foreground">Level Profile</div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        );
      case "settings":
        return (
          <div className="h-full overflow-y-auto p-6">
            <h2 className="text-2xl font-bold mb-4">Settings</h2>
            
            {/* System Status */}
            {systemHealth && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Backend Status:</span>
                      <Badge variant={systemHealth.status === 'healthy' ? 'default' : 'secondary'}>
                        {systemHealth.status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>ChromaDB:</span>
                      <Badge variant={systemHealth.chroma_available ? 'default' : 'destructive'}>
                        {systemHealth.chroma_available ? 'Available' : 'Unavailable'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Configuration:</span>
                      <Badge variant={systemHealth.config_available ? 'default' : 'destructive'}>
                        {systemHealth.config_available ? 'Loaded' : 'Missing'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Downloads Directory:</span>
                      <Badge variant={systemHealth.downloads_available ? 'default' : 'destructive'}>
                        {systemHealth.downloads_available ? 'Available' : 'Missing'}
                      </Badge>
                    </div>
                  </div>
                  <Button onClick={checkSystemHealth} className="mt-4" size="sm">
                    Refresh Status
                  </Button>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent className="p-8 text-center">
                <Settings className="h-16 w-16 mx-auto mb-4 text-gray-500" />
                <h3 className="text-xl font-semibold mb-2">Application Settings</h3>
                <p className="text-muted-foreground">
                  Configure your FloatChat preferences and system settings
                </p>
              </CardContent>
            </Card>
          </div>
        );
      default:
        return renderChatContent();
    }
  };

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? "w-64" : "w-16"} bg-white border-r transition-all duration-300 flex flex-col`}>
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center">
              <Waves className="h-6 w-6 text-blue-600 mr-2" />
              <span className="font-bold text-blue-900">FloatChat</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            {sidebarItems.map((item) => (
              <Button
                key={item.id}
                variant={activeTab === item.id ? "default" : "ghost"}
                className={`w-full justify-start ${!sidebarOpen && "px-2"}`}
                onClick={() => setActiveTab(item.id)}
              >
                <item.icon className="h-4 w-4" />
                {sidebarOpen && <span className="ml-2">{item.label}</span>}
              </Button>
            ))}
          </div>
        </nav>

        {/* User Info */}
        <div className="p-4 border-t">
          {sidebarOpen ? (
            <div className="space-y-3">
              <div className="text-sm text-muted-foreground">
                <p>Logged in as</p>
                <p className="font-medium">{user?.email || "Demo User"}</p>
              </div>
              {user && (
                <Button 
                  onClick={handleLogout} 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-medium text-blue-600">
                  {user?.email ? user.email.charAt(0).toUpperCase() : "DU"}
                </span>
              </div>
              {user && (
                <Button 
                  onClick={handleLogout} 
                  variant="ghost" 
                  size="sm" 
                  className="w-8 h-8 p-0"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-14 border-b flex items-center justify-between px-6">
          <h1 className="font-semibold capitalize">
            {sidebarItems.find(item => item.id === activeTab)?.label || "Dashboard"}
          </h1>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              <Calendar className="h-3 w-3 mr-1" />
              Live Data
            </Badge>
            {systemHealth && (
              <Badge 
                variant={systemHealth.status === 'healthy' ? 'default' : 'secondary'}
              >
                {systemHealth.status === 'healthy' ? '🟢' : '🟡'} System
              </Badge>
            )}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default FloatChatAppEnhanced;
