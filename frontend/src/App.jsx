import { useState, useEffect } from "react";

function App() {
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [merchant, setMerchant] = useState("");
  const [description, setDescription] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  const [notes, setNotes] = useState("");

  const [expenses, setExpenses] = useState([]);

  useEffect(() => {
    async function fetchExpenses() {
      const response = await fetch("http://127.0.0.1:8000/expenses");
      const data = await response.json();

      setExpenses(data);
    }

    fetchExpenses();
  }, []);

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
      const newExpense = await response.json();

      setExpenses((currentExpenses) => [newExpense, ...currentExpenses]);

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

  async function handleDelete(expenseId) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this expense?",
    );

    if (!confirmed) {
      return;
    }

    const response = await fetch(
      `http://127.0.0.1:8000/expenses/${expenseId}`,
      {
        method: "DELETE",
      },
    );

    if (response.ok) {
      setExpenses((currentExpenses) =>
        currentExpenses.filter((expense) => expense.id !== expenseId),
      );
    } else {
      console.log("Failed to delete expense");
    }
  }

  const totalSpentCents = expenses.reduce(
    (total, expense) => total + expense.amount_cents,
    0,
  );

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
            min="0.01"
            required
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </div>

        <div>
          <label>Category</label>
          <select
            value={category}
            required
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">Select a category</option>
            <option value="Groceries">Groceries</option>
            <option value="Restaurants">Restaurants</option>
            <option value="Transportation">Transportation</option>
            <option value="Housing">Housing</option>
            <option value="Utilities">Utilities</option>
            <option value="Health">Health</option>
            <option value="Shopping">Shopping</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Education">Education</option>
            <option value="Other">Other</option>
          </select>
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
            required
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

      <h2>Expenses</h2>
      <p>
        <strong>Total spent: ${(totalSpentCents / 100).toFixed(2)}</strong>
      </p>

      {expenses.length === 0 ? (
        <p>No expenses yet.</p>
      ) : (
        <div>
          {expenses.map((expense) => (
            <div key={expense.id}>
              <h3>{expense.merchant || "Unknown Merchant"}</h3>

              <p>${(expense.amount_cents / 100).toFixed(2)}</p>

              <p>{expense.category}</p>

              <p>{expense.purchase_date}</p>

              <button type="button" onClick={() => handleDelete(expense.id)}>
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
