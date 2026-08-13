import { Routes, Route, Link } from "react-router-dom";
import { Home, FileText, Bell, LogOut } from "lucide-react";
import Invoices from "./Invoices";
import Updates from "./Updates";

const Sidebar = () => (
  <div className="bg-gray-100 w-64 min-h-screen p-4">
    <h1 className="text-2xl font-bold mb-6">User Portal</h1>
    <nav>
      <ul>
        <li className="mb-2">
          <Link to="/user" className="flex items-center p-2 rounded hover:bg-gray-200">
            <FileText className="h-4 w-4 mr-2" />
            <span>Invoices</span>
          </Link>
        </li>
        <li className="mb-2">
          <Link to="/user/updates" className="flex items-center p-2 rounded hover:bg-gray-200">
            <Bell className="h-4 w-4 mr-2" />
            <span>Updates</span>
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

const UserDashboard = () => (
  <div className="flex">
    <Sidebar />
    <main className="flex-1 p-6">
      <Routes>
        <Route index element={<Invoices />} />
        <Route path="updates" element={<Updates />} />
      </Routes>
    </main>
  </div>
);

export default UserDashboard;
