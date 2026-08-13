import { useState } from "react";
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
  LogOut
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/useAuth.jsx";
import { toast } from "sonner";
import argoFloatImage from '@/assets/argo-float.jpg';
import oceanProfilesImage from '@/assets/ocean-profiles.jpg';
import oceanSensorsImage from '@/assets/ocean-sensors.jpg';
import argoGlobalMapImage from '@/assets/argo-global-map.jpg';

const FloatChatApp = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("chat");
  const [chatMessage, setChatMessage] = useState("");
  const { user, signOut } = useAuth();
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "system",
      content: "Welcome to FloatChat! I can help you explore ARGO ocean data. Try asking: 'Show me temperature profiles near the equator'"
    }
  ]);

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

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return;
    
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: "user",
      content: chatMessage
    }]);
    
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: "assistant",
        content: "I understand you're looking for ocean data. Let me help you with that query. This would typically connect to our AI system for real-time analysis."
      }]);
    }, 1000);
    
    setChatMessage("");
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
              {message.content}
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
          />
          <Button onClick={handleSendMessage}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          <Badge variant="outline" className="cursor-pointer text-xs">
            Temperature profiles equator
          </Badge>
          <Badge variant="outline" className="cursor-pointer text-xs">
            Salinity Arabian Sea
          </Badge>
          <Badge variant="outline" className="cursor-pointer text-xs">
            Pressure profiles Pacific
          </Badge>
        </div>
      </div>
    </div>
  );

  const renderAnalyticsContent = () => (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Ocean Data Analytics</h2>
        <div className="relative w-16 h-16 rounded-lg overflow-hidden">
          <img src={oceanSensorsImage} alt="Ocean Sensors" className="w-full h-full object-cover" />
        </div>
      </div>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
    </div>
  );

  const renderMapContent = () => (
    <div className="p-6 space-y-4">
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
      <Card>
        <CardContent className="p-0">
          <div className="relative h-[600px] rounded-lg overflow-hidden">
            <img src={argoGlobalMapImage} alt="Global ARGO Map" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
              <div className="text-center text-white">
                <Map className="h-16 w-16 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">Interactive Ocean Map</h3>
                <p>Global ARGO float positions and trajectories</p>
                <div className="mt-6 flex gap-4 justify-center">
                  <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
                    1,234 Active Floats
                  </Badge>
                  <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
                    Real-time Data
                  </Badge>
                </div>
                <p className="text-sm opacity-90 mt-4">(Interactive map integration available with backend)</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">Indian Ocean</div>
            <div className="text-sm text-muted-foreground">Primary Focus Region</div>
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
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">NDVI Analysis</h2>
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
          <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold mb-4">Ocean Profiles</h2>
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
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
          </div>
        );
      case "settings":
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">Settings</h2>
            <Card>
              <CardContent className="p-8 text-center">
                <Settings className="h-16 w-16 mx-auto mb-4 text-gray-500" />
                <h3 className="text-xl font-semibold mb-2">Application Settings</h3>
                <p className="text-muted-foreground">
                  Configure your FloatChat preferences
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
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default FloatChatApp;