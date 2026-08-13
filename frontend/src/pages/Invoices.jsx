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

const Invoices = () => {
  const [invoices, setInvoices] = useState([
    { id: 1, amount: 1000, status: "Paid", date: "2023-03-01" },
    { id: 2, amount: 1500, status: "Pending", date: "2023-03-15" },
    { id: 3, amount: 800, status: "Overdue", date: "2023-02-28" },
  ]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Your Invoices</h1>
      <div className="mb-4">
        <Input placeholder="Search invoices..." className="max-w-sm" />
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Invoice ID</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {invoices.map((invoice) => (
            <TableRow key={invoice.id}>
              <TableCell>{invoice.id}</TableCell>
              <TableCell>${invoice.amount}</TableCell>
              <TableCell>{invoice.status}</TableCell>
              <TableCell>{invoice.date}</TableCell>
              <TableCell>
                <Button variant="outline" size="sm">
                  View Details
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default Invoices;
