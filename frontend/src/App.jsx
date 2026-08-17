import { useState, useEffect } from "react";
import "./App.css";

function getCurrentMonth() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");

  return `${year}-${month}`;
}

function getTodayDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function formatDate(dateString) {
  const [year, month, day] = dateString.split("-").map(Number);

  const localDate = new Date(year, month - 1, day);

  return localDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function App() {
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [merchant, setMerchant] = useState("");
  const [description, setDescription] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(getTodayDate);
  const [notes, setNotes] = useState("");

  const [expenses, setExpenses] = useState([]);
  const [editingExpenseId, setEditingExpenseId] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [budgetAmount, setBudgetAmount] = useState("");
  const [monthlyBudgetCents, setMonthlyBudgetCents] = useState(null);

  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [selectedExpenseForItems, setSelectedExpenseForItems] = useState(null);

  const [expenseItems, setExpenseItems] = useState([]);
  const [isLoadingItems, setIsLoadingItems] = useState(false);

  const [itemName, setItemName] = useState("");
  const [itemQuantity, setItemQuantity] = useState("1");
  const [itemUnit, setItemUnit] = useState("each");
  const [itemUnitPrice, setItemUnitPrice] = useState("");

  const [isEditingItemList, setIsEditingItemList] = useState(false);
  const [editingItemId, setEditingItemId] = useState(null);

  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [isLoadingPriceHistory, setIsLoadingPriceHistory] = useState(false);

  useEffect(() => {
    async function fetchExpenses() {
      const response = await fetch("http://127.0.0.1:8000/expenses");
      const data = await response.json();

      setExpenses(data);
    }

    fetchExpenses();
  }, []);

  useEffect(() => {
    async function fetchMonthlyBudget() {
      if (!selectedMonth) {
        setMonthlyBudgetCents(null);
        setBudgetAmount("");
        return;
      }

      const response = await fetch(
        `http://127.0.0.1:8000/budgets/${selectedMonth}`,
      );

      if (response.ok) {
        const data = await response.json();

        setMonthlyBudgetCents(data.amount_cents);
        setBudgetAmount((data.amount_cents / 100).toFixed(2));
      } else if (response.status === 404) {
        setMonthlyBudgetCents(null);
        setBudgetAmount("");
      } else {
        console.log("Failed to load monthly budget");
      }
    }

    fetchMonthlyBudget();
  }, [selectedMonth]);

  function resetForm() {
    setEditingExpenseId(null);
    setAmount("");
    setCategory("");
    setMerchant("");
    setDescription("");
    setPurchaseDate(getTodayDate());
    setNotes("");
  }

  function openAddExpenseModal() {
    resetForm();
    setIsExpenseModalOpen(true);
  }

  function closeExpenseModal() {
    resetForm();
    setIsExpenseModalOpen(false);
  }

  function resetItemForm() {
    setItemName("");
    setItemQuantity("1");
    setItemUnit("each");
    setItemUnitPrice("");
  }

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

    const isEditing = editingExpenseId !== null;

    const url = isEditing
      ? `http://127.0.0.1:8000/expenses/${editingExpenseId}`
      : "http://127.0.0.1:8000/expenses";

    const method = isEditing ? "PUT" : "POST";

    const response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(expenseData),
    });

    if (response.ok) {
      const savedExpense = await response.json();

      if (isEditing) {
        setExpenses((currentExpenses) =>
          currentExpenses.map((expense) =>
            expense.id === savedExpense.id ? savedExpense : expense,
          ),
        );
      } else {
        setExpenses((currentExpenses) => [savedExpense, ...currentExpenses]);
      }

      closeExpenseModal();
    } else {
      console.log("Failed to save expense");
    }
  }

  async function handleBudgetSubmit(event) {
    event.preventDefault();

    if (!selectedMonth) {
      return;
    }

    const budgetData = {
      amount_cents: Math.round(Number(budgetAmount) * 100),
    };

    const response = await fetch(
      `http://127.0.0.1:8000/budgets/${selectedMonth}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(budgetData),
      },
    );

    if (response.ok) {
      const savedBudget = await response.json();

      setMonthlyBudgetCents(savedBudget.amount_cents);
      setBudgetAmount((savedBudget.amount_cents / 100).toFixed(2));
    } else {
      console.log("Failed to save monthly budget");
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

  async function openItemsModal(expense) {
    setIsEditingItemList(false);
    setEditingItemId(null);
    resetItemForm();
    setSelectedExpenseForItems(expense);
    setExpenseItems([]);
    setIsLoadingItems(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/expenses/${expense.id}/items`,
      );

      if (response.ok) {
        const data = await response.json();
        setExpenseItems(data);
      } else {
        console.log("Failed to load expense items");
      }
    } catch (error) {
      console.log("Failed to connect to the API", error);
    } finally {
      setIsLoadingItems(false);
    }
  }

  async function openPriceHistory(item) {
    setSelectedHistoryItem(item);
    setPriceHistory([]);
    setIsLoadingPriceHistory(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/items/price-history?name=${encodeURIComponent(
          item.name,
        )}`,
      );

      if (response.ok) {
        const data = await response.json();
        setPriceHistory(data);
      } else {
        console.log("Failed to load price history");
      }
    } catch (error) {
      console.log("Failed to connect to the API", error);
    } finally {
      setIsLoadingPriceHistory(false);
    }
  }

  function closePriceHistory() {
    setSelectedHistoryItem(null);
    setPriceHistory([]);
  }
  async function handleDeleteItem(itemId) {
    if (!selectedExpenseForItems) {
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete this item?",
    );

    if (!confirmed) {
      return;
    }

    const response = await fetch(
      `http://127.0.0.1:8000/expenses/${selectedExpenseForItems.id}/items/${itemId}`,
      {
        method: "DELETE",
      },
    );

    if (response.ok) {
      setExpenseItems((currentItems) =>
        currentItems.filter((item) => item.id !== itemId),
      );

      if (editingItemId === itemId) {
        setEditingItemId(null);
        resetItemForm();
      }
    } else {
      console.log("Failed to delete item");
    }
  }

  function handleCancelItemEdit() {
    setEditingItemId(null);
    resetItemForm();
  }

  function handleStartEditingItem(item) {
    setEditingItemId(item.id);
    setItemName(item.name);
    setItemQuantity(String(item.quantity));
    setItemUnit(item.unit);
    setItemUnitPrice((item.unit_price_cents / 100).toFixed(2));
  }

  async function handleAddItem(event) {
    event.preventDefault();

    if (!selectedExpenseForItems) {
      return;
    }

    const itemData = {
      name: itemName.trim(),
      quantity: Number(itemQuantity),
      unit: itemUnit,
      unit_price_cents: Math.round(Number(itemUnitPrice) * 100),
    };

    const isEditingItem = editingItemId !== null;

    const url = isEditingItem
      ? `http://127.0.0.1:8000/expenses/${selectedExpenseForItems.id}/items/${editingItemId}`
      : `http://127.0.0.1:8000/expenses/${selectedExpenseForItems.id}/items`;

    const response = await fetch(url, {
      method: isEditingItem ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(itemData),
    });

    if (response.ok) {
      const savedItem = await response.json();

      if (isEditingItem) {
        setExpenseItems((currentItems) =>
          currentItems.map((item) =>
            item.id === savedItem.id ? savedItem : item,
          ),
        );
      } else {
        setExpenseItems((currentItems) => [...currentItems, savedItem]);
      }

      setEditingItemId(null);
      resetItemForm();
    } else {
      console.log("Failed to save item");
    }
  }

  function closeItemsModal() {
    setSelectedExpenseForItems(null);
    setExpenseItems([]);
    setIsEditingItemList(false);
    setEditingItemId(null);
    setSelectedHistoryItem(null);
    setPriceHistory([]);
    setIsLoadingPriceHistory(false);
    resetItemForm();
  }

  function handleEdit(expense) {
    setEditingExpenseId(expense.id);
    setAmount((expense.amount_cents / 100).toFixed(2));
    setCategory(expense.category);
    setMerchant(expense.merchant || "");
    setDescription(expense.description || "");
    setPurchaseDate(expense.purchase_date);
    setNotes(expense.notes || "");

    setIsExpenseModalOpen(true);
  }

  function toggleItemListEditing() {
    setIsEditingItemList((currentMode) => !currentMode);
    setEditingItemId(null);
    resetItemForm();
  }

  const filteredExpenses = expenses.filter((expense) => {
    const matchesMonth =
      !selectedMonth || expense.purchase_date.startsWith(selectedMonth);

    const matchesCategory =
      selectedCategory === "All" || expense.category === selectedCategory;

    return matchesMonth && matchesCategory;
  });

  const totalSpentCents = filteredExpenses.reduce(
    (total, expense) => total + expense.amount_cents,
    0,
  );

  const monthlySpentCents = expenses
    .filter(
      (expense) =>
        !selectedMonth || expense.purchase_date.startsWith(selectedMonth),
    )
    .reduce((total, expense) => total + expense.amount_cents, 0);

  const remainingBudgetCents =
    monthlyBudgetCents === null ? null : monthlyBudgetCents - monthlySpentCents;

  const budgetUsedPercent =
    monthlyBudgetCents === null
      ? 0
      : (monthlySpentCents / monthlyBudgetCents) * 100;

  const progressWidth = Math.min(budgetUsedPercent, 100);

  const isOverBudget =
    remainingBudgetCents !== null && remainingBudgetCents < 0;

  const itemSubtotalCents = expenseItems.reduce(
    (total, item) =>
      total + Math.round(Number(item.quantity) * item.unit_price_cents),
    0,
  );

  const unaccountedCents = selectedExpenseForItems
    ? selectedExpenseForItems.amount_cents - itemSubtotalCents
    : 0;

  return (
    <main className="app">
      <header className="app-header">
        <div>
          <h1>Budget</h1>
          <p>Track your spending without connecting your bank.</p>
        </div>

        <button
          className="add-transaction-button"
          type="button"
          onClick={openAddExpenseModal}
        >
          + Add New Transaction
        </button>
      </header>

      {isExpenseModalOpen && (
        <div className="modal-overlay" onMouseDown={closeExpenseModal}>
          <section
            className="expense-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="transaction-modal-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <p>Transaction</p>

                <h2 id="transaction-modal-title">
                  {editingExpenseId === null
                    ? "Add New Transaction"
                    : "Edit Transaction"}
                </h2>
              </div>

              <button
                className="modal-close"
                type="button"
                aria-label="Close transaction form"
                onClick={closeExpenseModal}
              >
                ×
              </button>
            </div>

            <form className="expense-form" onSubmit={handleSubmit}>
              {" "}
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
              <button type="submit">
                {editingExpenseId === null ? "Add Transaction" : "Save Changes"}
              </button>
              {editingExpenseId !== null && (
                <button type="button" onClick={closeExpenseModal}>
                  Cancel
                </button>
              )}
            </form>
          </section>
        </div>
      )}

      {selectedExpenseForItems && (
        <div className="modal-overlay" onMouseDown={closeItemsModal}>
          <section
            className="expense-modal items-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="items-modal-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <p>Transaction items</p>

                <h2 id="items-modal-title">
                  {selectedExpenseForItems.merchant || "Unknown Merchant"}
                </h2>
              </div>

              <div className="items-header-actions">
                {expenseItems.length > 0 && (
                  <button
                    className={`edit-items-toggle ${isEditingItemList ? "active" : ""}`}
                    type="button"
                    onClick={toggleItemListEditing}
                  >
                    {isEditingItemList ? "Done" : "Edit List"}
                  </button>
                )}

                <button
                  className="modal-close"
                  type="button"
                  aria-label="Close items"
                  onClick={closeItemsModal}
                >
                  ×
                </button>
              </div>
            </div>

            <p className="items-transaction-total">
              Transaction total:{" "}
              <strong>
                ${(selectedExpenseForItems.amount_cents / 100).toFixed(2)}
              </strong>
            </p>

            <div className="item-balance">
              <div>
                <span>Items entered</span>
                <strong>${(itemSubtotalCents / 100).toFixed(2)}</strong>
              </div>

              <div
                className={
                  unaccountedCents === 0
                    ? "item-balance-complete"
                    : unaccountedCents < 0
                      ? "item-balance-over"
                      : ""
                }
              >
                <span>{unaccountedCents < 0 ? "Over by" : "Unaccounted"}</span>

                <strong>
                  ${(Math.abs(unaccountedCents) / 100).toFixed(2)}
                </strong>
              </div>
            </div>

            {editingItemId === null && (
              <form className="item-form" onSubmit={handleAddItem}>
                <div className="item-name-field">
                  <label htmlFor="item-name">Item name</label>

                  <input
                    id="item-name"
                    type="text"
                    required
                    placeholder="Milk"
                    value={itemName}
                    onChange={(event) => setItemName(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="item-quantity">Quantity</label>

                  <input
                    id="item-quantity"
                    type="number"
                    min="0.01"
                    step="0.01"
                    required
                    value={itemQuantity}
                    onChange={(event) => setItemQuantity(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="item-unit">Unit</label>

                  <select
                    id="item-unit"
                    value={itemUnit}
                    onChange={(event) => setItemUnit(event.target.value)}
                  >
                    <option value="each">Each</option>
                    <option value="pack">Pack</option>
                    <option value="lb">Pound</option>
                    <option value="oz">Ounce</option>
                    <option value="gallon">Gallon</option>
                    <option value="liter">Liter</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="item-price">Unit price</label>

                  <input
                    id="item-price"
                    type="number"
                    min="0.01"
                    step="0.01"
                    required
                    placeholder="3.99"
                    value={itemUnitPrice}
                    onChange={(event) => setItemUnitPrice(event.target.value)}
                  />
                </div>
                <button type="submit">
                  {editingItemId === null ? "Add Item" : "Save Item"}
                </button>{" "}
              </form>
            )}
            {isLoadingItems ? (
              <p className="items-message">Loading items...</p>
            ) : expenseItems.length === 0 ? (
              <p className="items-message">
                No items have been added to this transaction.
              </p>
            ) : (
              <div className="items-list">
                {expenseItems.map((item) =>
                  editingItemId === item.id ? (
                    <form
                      className="item-row-edit-form"
                      key={item.id}
                      onSubmit={handleAddItem}
                    >
                      <input
                        type="text"
                        required
                        aria-label="Item name"
                        value={itemName}
                        onChange={(event) => setItemName(event.target.value)}
                      />

                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                        aria-label="Quantity"
                        value={itemQuantity}
                        onChange={(event) =>
                          setItemQuantity(event.target.value)
                        }
                      />

                      <select
                        aria-label="Unit"
                        value={itemUnit}
                        onChange={(event) => setItemUnit(event.target.value)}
                      >
                        <option value="each">Each</option>
                        <option value="pack">Pack</option>
                        <option value="lb">Pound</option>
                        <option value="oz">Ounce</option>
                        <option value="gallon">Gallon</option>
                        <option value="liter">Liter</option>
                      </select>

                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                        aria-label="Unit price"
                        value={itemUnitPrice}
                        onChange={(event) =>
                          setItemUnitPrice(event.target.value)
                        }
                      />

                      <div className="inline-item-actions">
                        <button className="inline-save-button" type="submit">
                          Save
                        </button>

                        <button
                          className="inline-cancel-button"
                          type="button"
                          onClick={handleCancelItemEdit}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="item-row" key={item.id}>
                      <div className="item-details">
                        <strong>{item.name}</strong>

                        <span>
                          {item.quantity} {item.unit} × $
                          {(item.unit_price_cents / 100).toFixed(2)}
                        </span>
                      </div>

                      <div className="item-row-end">
                        <strong className="item-row-total">
                          $
                          {(
                            (item.quantity * item.unit_price_cents) /
                            100
                          ).toFixed(2)}
                        </strong>
                        <button
                          className="item-history-button"
                          type="button"
                          onClick={() => openPriceHistory(item)}
                        >
                          History
                        </button>
                        {isEditingItemList && (
                          <div className="item-row-actions">
                            <button
                              className="item-edit-button"
                              type="button"
                              onClick={() => handleStartEditingItem(item)}
                            >
                              Edit
                            </button>

                            <button
                              className="item-delete-button"
                              type="button"
                              onClick={() => handleDeleteItem(item.id)}
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ),
                )}
              </div>
            )}
          </section>
        </div>
      )}

      {selectedHistoryItem && (
        <div
          className="modal-overlay price-history-overlay"
          onMouseDown={closePriceHistory}
        >
          <section
            className="expense-modal price-history-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="price-history-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <p>Price tracking</p>

                <h2 id="price-history-title">
                  {selectedHistoryItem.name} history
                </h2>
              </div>

              <button
                className="modal-close"
                type="button"
                aria-label="Close price history"
                onClick={closePriceHistory}
              >
                ×
              </button>
            </div>

            {isLoadingPriceHistory ? (
              <p className="items-message">Loading price history...</p>
            ) : priceHistory.length === 0 ? (
              <p className="items-message">
                No previous purchases found for this item.
              </p>
            ) : (
              <div className="price-history-list">
                {priceHistory.map((entry) => (
                  <div className="price-history-row" key={entry.item_id}>
                    <div>
                      <strong>{formatDate(entry.purchase_date)}</strong>
                      <span>{entry.merchant || "Unknown Merchant"}</span>
                    </div>

                    <div>
                      <strong>
                        ${(entry.unit_price_cents / 100).toFixed(2)}
                      </strong>

                      <span>
                        {entry.quantity} {entry.unit}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      <h2>Expenses</h2>
      <div className="expense-toolbar">
        <div className="filter-control">
          <label htmlFor="month-filter">Month</label>

          <input
            id="month-filter"
            type="month"
            value={selectedMonth}
            onChange={(event) => setSelectedMonth(event.target.value)}
          />
        </div>

        <div className="filter-control">
          <label htmlFor="category-filter">Category</label>

          <select
            id="category-filter"
            value={selectedCategory}
            onChange={(event) => setSelectedCategory(event.target.value)}
          >
            <option value="All">All categories</option>
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
      </div>

      <form className="budget-form" onSubmit={handleBudgetSubmit}>
        <div className="budget-field">
          <label htmlFor="budget-amount">Monthly budget</label>

          <div className="budget-input">
            <span>$</span>

            <input
              id="budget-amount"
              type="number"
              min="0.01"
              step="0.01"
              required
              placeholder="500.00"
              value={budgetAmount}
              onChange={(event) => setBudgetAmount(event.target.value)}
            />
          </div>
        </div>

        <button type="submit">
          {monthlyBudgetCents === null ? "Set Budget" : "Update Budget"}
        </button>
      </form>

      <div className="summary-card">
        <span>
          {selectedCategory === "All"
            ? "Total spent"
            : `${selectedCategory} spent`}
        </span>{" "}
        <strong>${(totalSpentCents / 100).toFixed(2)}</strong>
      </div>

      {monthlyBudgetCents !== null && (
        <section
          className={`budget-status ${isOverBudget ? "over-budget" : ""}`}
        >
          <div className="budget-stats">
            <div className="budget-stat">
              <span>Monthly budget</span>
              <strong>${(monthlyBudgetCents / 100).toFixed(2)}</strong>
            </div>

            <div className="budget-stat">
              <span>Spent this month</span>
              <strong>${(monthlySpentCents / 100).toFixed(2)}</strong>
            </div>

            <div className="budget-stat">
              <span>{isOverBudget ? "Over budget" : "Remaining"}</span>

              <strong>
                ${(Math.abs(remainingBudgetCents) / 100).toFixed(2)}
              </strong>
            </div>
          </div>

          <div className="budget-progress">
            <div
              className="budget-progress-fill"
              style={{
                width: `${progressWidth}%`,
              }}
            />
          </div>

          <p className="budget-progress-text">
            {budgetUsedPercent.toFixed(0)}% of the monthly budget used
          </p>
        </section>
      )}

      {filteredExpenses.length === 0 ? (
        <p className="empty-message">No expenses found for this month.</p>
      ) : (
        <div>
          {filteredExpenses.length === 0 ? (
            <p className="empty-message">No expenses yet.</p>
          ) : (
            <div className="expense-list">
              {filteredExpenses.map((expense) => (
                <article className="expense-card" key={expense.id}>
                  <div className="expense-card-header">
                    <div>
                      <p className="expense-category">{expense.category}</p>

                      <h3>{expense.merchant || "Unknown Merchant"}</h3>
                    </div>

                    <p className="expense-amount">
                      ${(expense.amount_cents / 100).toFixed(2)}
                    </p>
                  </div>

                  {expense.description && (
                    <p className="expense-description">{expense.description}</p>
                  )}

                  {expense.notes && (
                    <p className="expense-notes">{expense.notes}</p>
                  )}

                  <p className="expense-date">
                    {formatDate(expense.purchase_date)}
                  </p>

                  <div className="expense-actions">
                    <button
                      className="items-button"
                      type="button"
                      onClick={() => openItemsModal(expense)}
                    >
                      Items
                    </button>
                    <button
                      className="edit-button"
                      type="button"
                      onClick={() => handleEdit(expense)}
                    >
                      Edit
                    </button>

                    <button
                      className="delete-button"
                      type="button"
                      onClick={() => handleDelete(expense.id)}
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}

export default App;
