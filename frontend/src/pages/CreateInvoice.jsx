import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const CreateInvoice = () => {
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState({
    customerName: "",
    amount: "",
    dueDate: "",
    status: "pending",
    description: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setInvoice((prev) => ({ ...prev, [name]: value }));
  };

  const handleStatusChange = (value) => {
    setInvoice((prev) => ({ ...prev, status: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the invoice data to your backend
    console.log("Invoice created:", invoice);
    // Navigate back to the dashboard or invoices list
    navigate("/admin");
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Create New Invoice</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="customerName">Customer Name</Label>
          <Input
            id="customerName"
            name="customerName"
            value={invoice.customerName}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <Label htmlFor="amount">Amount</Label>
          <Input
            id="amount"
            name="amount"
            type="number"
            value={invoice.amount}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <Label htmlFor="dueDate">Due Date</Label>
          <Input
            id="dueDate"
            name="dueDate"
            type="date"
            value={invoice.dueDate}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <Label htmlFor="status">Status</Label>
          <Select onValueChange={handleStatusChange} defaultValue={invoice.status}>
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
              <SelectItem value="overdue">Overdue</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            name="description"
            value={invoice.description}
            onChange={handleChange}
            rows={4}
          />
        </div>
        <Button type="submit">Create Invoice</Button>
      </form>
    </div>
  );
};

export default CreateInvoice;
