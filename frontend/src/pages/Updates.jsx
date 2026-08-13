import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Updates = () => {
  const [updates, setUpdates] = useState([
    { id: 1, content: "Your invoice #1234 has been paid", date: "2023-03-01" },
    { id: 2, content: "New feature: You can now download invoice PDFs", date: "2023-02-28" },
    { id: 3, content: "Reminder: Invoice #5678 is due next week", date: "2023-02-25" },
  ]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Your Updates</h1>
      <div>
        {updates.map((update) => (
          <Card key={update.id} className="mb-4">
            <CardHeader>
              <CardTitle>{update.date}</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{update.content}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Updates;
