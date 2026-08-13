import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const LandingPage = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <h1 className="text-4xl font-bold mb-8">Welcome to Our Agency Portal</h1>
      <div className="space-x-4">
        <Button asChild>
          <Link to="/admin">Admin Login</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/user">User Login</Link>
        </Button>
      </div>
    </div>
  );
};

export default LandingPage;
