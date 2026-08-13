import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth.jsx";
import AuthGuard from "./components/AuthGuard";
import LandingPage from "./pages/LandingPage";
import AdminDashboard from "./pages/AdminDashboard";
import UserDashboard from "./pages/UserDashboard";
import FloatChatDashboard from "./pages/FloatChatDashboard";
import FloatChatLogin from "./pages/FloatChatLogin";
import FloatChatSignup from "./pages/FloatChatSignup";
import FloatChatApp from "./pages/FloatChatAppEnhanced";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<FloatChatDashboard />} />
            <Route path="/login" element={<FloatChatLogin />} />
            <Route path="/signup" element={<FloatChatSignup />} />
            <Route path="/chat" element={<AuthGuard><FloatChatApp /></AuthGuard>} />
            <Route path="/demo" element={<FloatChatApp />} />
            <Route path="/admin/*" element={<AdminDashboard />} />
            <Route path="/user/*" element={<UserDashboard />} />
            <Route path="/legacy" element={<LandingPage />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
