import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const Customers = () => {
  const [customers, setCustomers] = useState([
    { id: 1, name: "Acme Corp", email: "contact@acme.com", totalInvoices: 5 },
    { id: 2, name: "Globex", email: "info@globex.com", totalInvoices: 3 },
    { id: 3, name: "Initech", email: "hello@initech.com", totalInvoices: 2 },
  ]);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Customers</h1>
        <Button>Add Customer</Button>
      </div>
      <div className="mb-4">
        <Input placeholder="Search customers..." className="max-w-sm" />
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Total Invoices</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {customers.map((customer) => (
            <TableRow key={customer.id}>
              <TableCell>{customer.id}</TableCell>
              <TableCell>{customer.name}</TableCell>
              <TableCell>{customer.email}</TableCell>
              <TableCell>{customer.totalInvoices}</TableCell>
              <TableCell>
                <Button variant="outline" size="sm" className="mr-2">
                  View
                </Button>
                <Button variant="outline" size="sm">
                  Edit
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default Customers;
