import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  BarChart3, 
  Map, 
  MessageSquare, 
  Waves, 
  Thermometer, 
  Droplets,
  TrendingUp,
  Globe,
  Calendar,
  LogOut
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth.jsx";
import { toast } from "sonner";

const FloatChatDashboard = () => {
  const { user, signOut } = useAuth();

  const handleLogout = async () => {
    const { error } = await signOut();
    if (error) {
      toast.error("Failed to sign out");
    } else {
      toast.success("Successfully signed out");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-blue-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-blue-900 mb-2">
                FloatChat
              </h1>
              <p className="text-lg text-blue-700">
                AI-Powered ARGO Ocean Data Discovery & Visualization
              </p>
            </div>
            <div className="flex gap-3">
              {user ? (
                <>
                  <span className="text-sm text-blue-700 flex items-center">
                    Welcome, {user.email}
                  </span>
                  <Button onClick={handleLogout} variant="outline">
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Button asChild variant="outline">
                    <Link to="/login">Login</Link>
                  </Button>
                  <Button asChild>
                    <Link to="/signup">Get Started</Link>
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <Card className="mb-8 bg-gradient-to-r from-blue-600 to-cyan-600 text-white border-0">
          <CardContent className="p-8">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h2 className="text-3xl font-bold mb-4">
                  Explore Ocean Data with Natural Language
                </h2>
                <p className="text-xl mb-6 opacity-90">
                  Ask questions about ARGO float data, visualize ocean profiles, 
                  and discover insights from the world's largest oceanographic dataset.
                </p>
                <Button asChild size="lg" variant="secondary">
                  <Link to="/chat">
                    <MessageSquare className="mr-2 h-5 w-5" />
                    Start Chatting
                  </Link>
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Card className="bg-white/10 border-white/20">
                  <CardContent className="p-4 text-center">
                    <Waves className="h-8 w-8 mx-auto mb-2" />
                    <h3 className="font-semibold">3M+ Profiles</h3>
                  </CardContent>
                </Card>
                <Card className="bg-white/10 border-white/20">
                  <CardContent className="p-4 text-center">
                    <Globe className="h-8 w-8 mx-auto mb-2" />
                    <h3 className="font-semibold">Global Coverage</h3>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
                AI Chat Interface
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Query ocean data using natural language. Ask complex questions 
                and get intelligent responses with visualizations.
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Map className="h-5 w-5 mr-2 text-green-600" />
                Interactive Maps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Visualize ARGO float trajectories, measurements, and ocean 
                parameters on interactive global maps.
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="h-5 w-5 mr-2 text-purple-600" />
                Advanced Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Generate depth profiles, time series, and comparative analysis 
                of temperature, salinity, and pressure parameters.
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Thermometer className="h-5 w-5 mr-2 text-red-600" />
                Temperature Profiles
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Explore ocean temperature variations across depths, regions, 
                and time periods with detailed CTD measurements.
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Droplets className="h-5 w-5 mr-2 text-cyan-600" />
                Salinity Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Analyze salinity patterns, compare regional differences, 
                and track changes in ocean composition over time.
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-orange-600" />
                NDVI Integration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Correlate ocean data with satellite vegetation indices 
                for comprehensive environmental analysis.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Example Queries */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Try These Example Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <Badge variant="outline" className="text-sm">
                  "Show me salinity profiles near the equator in March 2023"
                </Badge>
                <Badge variant="outline" className="text-sm">
                  "Compare pressure profiles in the Arabian Sea for the last 6 months"
                </Badge>
                <Badge variant="outline" className="text-sm">
                  "What are the nearest ARGO floats to latitude 20°N, longitude 65°E?"
                </Badge>
              </div>
              <div className="space-y-3">
                <Badge variant="outline" className="text-sm">
                  "Plot temperature-depth profiles for the Indian Ocean"
                </Badge>
                <Badge variant="outline" className="text-sm">
                  "Show seasonal variations in ocean pressure levels"
                </Badge>
                <Badge variant="outline" className="text-sm">
                  "Generate a map of all active floats in the Pacific"
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          <Card className="text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-blue-600 mb-2">4,000+</div>
              <div className="text-sm text-muted-foreground">Active Floats</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-cyan-600 mb-2">3M+</div>
              <div className="text-sm text-muted-foreground">Ocean Profiles</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-green-600 mb-2">20+</div>
              <div className="text-sm text-muted-foreground">Years of Data</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-purple-600 mb-2">Global</div>
              <div className="text-sm text-muted-foreground">Ocean Coverage</div>
            </CardContent>
          </Card>
        </div>

        {/* Call to Action */}
        <Card className="text-center bg-gradient-to-r from-blue-600 to-cyan-600 text-white border-0">
          <CardContent className="p-8">
            <h3 className="text-2xl font-bold mb-4">
              Ready to Explore Ocean Data?
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Start your journey into the world's most comprehensive ocean dataset
            </p>
            <div className="flex justify-center gap-4">
              <Button asChild size="lg" variant="secondary">
                <Link to="/signup">Create Account</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-600">
                <Link to="/demo">View Demo</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FloatChatDashboard;