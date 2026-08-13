import { Home, FileText, Users, Bell } from "lucide-react";
import Dashboard from "./pages/Dashboard.jsx";
import Invoices from "./pages/Invoices.jsx";
import Customers from "./pages/Customers.jsx";
import Updates from "./pages/Updates.jsx";

/**
 * Central place for defining the navigation items. Used for navigation components and routing.
 */
export const navItems = [
  {
    title: "Dashboard",
    to: "/",
    icon: <Home className="h-4 w-4" />,
    page: <Dashboard />,
  },
  {
    title: "Invoices",
    to: "/invoices",
    icon: <FileText className="h-4 w-4" />,
    page: <Invoices />,
  },
  {
    title: "Customers",
    to: "/customers",
    icon: <Users className="h-4 w-4" />,
    page: <Customers />,
  },
  {
    title: "Updates",
    to: "/updates",
    icon: <Bell className="h-4 w-4" />,
    page: <Updates />,
  },
];
