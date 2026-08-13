import { Routes, Route, Link } from "react-router-dom";
import { Home, FileText, Users, LogOut } from "lucide-react";
import Dashboard from "./Dashboard";
import Customers from "./Customers";
import CreateInvoice from "./CreateInvoice";

const Sidebar = () => (
  <div className="bg-gray-100 w-64 min-h-screen p-4">
    <h1 className="text-2xl font-bold mb-6">Admin Portal</h1>
    <nav>
      <ul>
        <li className="mb-2">
          <Link to="/admin" className="flex items-center p-2 rounded hover:bg-gray-200">
            <Home className="h-4 w-4 mr-2" />
            <span>Dashboard</span>
          </Link>
        </li>
        <li className="mb-2">
          <Link to="/admin/customers" className="flex items-center p-2 rounded hover:bg-gray-200">
            <Users className="h-4 w-4 mr-2" />
            <span>Customers</span>
          </Link>
        </li>
        <li className="mb-2">
          <Link to="/admin/create-invoice" className="flex items-center p-2 rounded hover:bg-gray-200">
            <FileText className="h-4 w-4 mr-2" />
            <span>Create Invoice</span>
          </Link>
        </li>
        <li className="mb-2">
          <Link to="/" className="flex items-center p-2 rounded hover:bg-gray-200">
            <LogOut className="h-4 w-4 mr-2" />
            <span>Logout</span>
          </Link>
        </li>
      </ul>
    </nav>
  </div>
);

const AdminDashboard = () => (
  <div className="flex">
    <Sidebar />
    <main className="flex-1 p-6">
      <Routes>
        <Route index element={<Dashboard />} />
        <Route path="customers" element={<Customers />} />
        <Route path="create-invoice" element={<CreateInvoice />} />
      </Routes>
    </main>
  </div>
);

export default AdminDashboard;
