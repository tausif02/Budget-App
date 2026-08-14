import { useState, useEffect } from "react";

function App() {
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [merchant, setMerchant] = useState("");
  const [description, setDescription] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  const [notes, setNotes] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    const expenseData = {
      amount_cents: Math.round(Number(amount) * 100),
      category: category,
      merchant: merchant || null,
      description: description || null,
      purchase_date: purchaseDate,
      notes: notes || null,
    };

    const response = await fetch("http://127.0.0.1:8000/expenses", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(expenseData),
    });

    if (response.ok) {
      console.log("Expense added successfully");

      setAmount("");
      setCategory("");
      setMerchant("");
      setDescription("");
      setPurchaseDate("");
      setNotes("");
    } else {
      console.log("Failed to add expense");
    }
  }

  return (
    <div>
      <h1>Budget</h1>
      <p>Track your spending without connecting your bank.</p>

      <h2>Add Expense</h2>

      <form onSubmit={handleSubmit}>
        <div>
          <label>Amount</label>
          <input
            type="number"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </div>

        <div>
          <label>Category</label>
          <input
            type="text"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          />
        </div>

        <div>
          <label>Merchant</label>
          <input
            type="text"
            value={merchant}
            onChange={(event) => setMerchant(event.target.value)}
          />
        </div>

        <div>
          <label>Description</label>
          <input
            type="text"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>

        <div>
          <label>Purchase Date</label>
          <input
            type="date"
            value={purchaseDate}
            onChange={(event) => setPurchaseDate(event.target.value)}
          />
        </div>

        <div>
          <label>Notes</label>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </div>

        <button type="submit">Add Expense</button>
      </form>
    </div>
  );
}

export default App;
