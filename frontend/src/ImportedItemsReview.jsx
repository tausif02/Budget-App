// ImportedItemsReview.jsx
import { useState } from "react";

function formatMoney(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

function ImportedItemsReview({ items, transactionAmountCents, onItemsChange }) {
  const [editorMode, setEditorMode] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);

  const [draftName, setDraftName] = useState("");
  const [draftQuantity, setDraftQuantity] = useState("1");
  const [draftUnit, setDraftUnit] = useState("each");
  const [draftPrice, setDraftPrice] = useState("");
  const [editorError, setEditorError] = useState("");

  const itemSubtotalCents = items.reduce(
    (total, item) =>
      total + Math.round(Number(item.quantity) * Number(item.unit_price_cents)),
    0,
  );

  const unaccountedCents = transactionAmountCents - itemSubtotalCents;

  const totalsMatch = unaccountedCents === 0;

  function resetEditor() {
    setEditorMode(null);
    setEditingIndex(null);
    setDraftName("");
    setDraftQuantity("1");
    setDraftUnit("each");
    setDraftPrice("");
    setEditorError("");
  }

  function startAddingItem() {
    resetEditor();
    setEditorMode("add");
  }

  function startEditingItem(item, itemIndex) {
    setEditorMode("edit");
    setEditingIndex(itemIndex);
    setDraftName(item.name);
    setDraftQuantity(String(item.quantity));
    setDraftUnit(item.unit);
    setDraftPrice((item.unit_price_cents / 100).toFixed(2));
    setEditorError("");
  }

  function saveDraftItem() {
    const cleanedName = draftName.trim();
    const quantity = Number(draftQuantity);
    const priceCents = Math.round(Number(draftPrice) * 100);

    if (!cleanedName) {
      setEditorError("Enter an item name.");
      return;
    }

    if (!Number.isFinite(quantity) || quantity <= 0) {
      setEditorError("Quantity must be greater than zero.");
      return;
    }

    if (!Number.isInteger(priceCents) || priceCents <= 0) {
      setEditorError("Unit price must be greater than zero.");
      return;
    }

    const savedItem = {
      name: cleanedName,
      quantity,
      unit: draftUnit,
      unit_price_cents: priceCents,
    };

    if (editorMode === "add") {
      onItemsChange([...items, savedItem]);
    } else {
      onItemsChange(
        items.map((item, itemIndex) =>
          itemIndex === editingIndex ? savedItem : item,
        ),
      );
    }

    resetEditor();
  }

  function deleteItem(itemIndex) {
    const item = items[itemIndex];

    const confirmed = window.confirm(`Remove "${item.name}" from this import?`);

    if (!confirmed) {
      return;
    }

    onItemsChange(
      items.filter((_, currentIndex) => currentIndex !== itemIndex),
    );

    if (editingIndex === itemIndex) {
      resetEditor();
    }
  }

  return (
    <section className="imported-items-review">
      <div className="imported-items-review-header">
        <div>
          <p>Receipt review</p>
          <h3>Review Imported Items</h3>
        </div>

        <button
          className="add-imported-item-button"
          type="button"
          onClick={startAddingItem}
        >
          + Add Missing Item
        </button>
      </div>

      <p className="imported-items-description">
        Check every detected item before saving the transaction. You can correct
        OCR mistakes or add anything that was missed.
      </p>

      <div className="imported-items-balance">
        <div>
          <span>Transaction total</span>
          <strong>{formatMoney(transactionAmountCents)}</strong>
        </div>

        <div>
          <span>Detected items</span>
          <strong>{formatMoney(itemSubtotalCents)}</strong>
        </div>

        <div
          className={
            totalsMatch
              ? "import-balance-complete"
              : unaccountedCents < 0
                ? "import-balance-over"
                : "import-balance-missing"
          }
        >
          <span>
            {totalsMatch
              ? "Balanced"
              : unaccountedCents < 0
                ? "Over by"
                : "Unaccounted"}
          </span>

          <strong>
            {totalsMatch ? "✓" : formatMoney(Math.abs(unaccountedCents))}
          </strong>
        </div>
      </div>

      {editorMode !== null && (
        <div className="imported-item-editor">
          <div className="imported-item-name-field">
            <label htmlFor="imported-item-name">Item name</label>

            <input
              id="imported-item-name"
              type="text"
              placeholder="Bananas"
              value={draftName}
              onChange={(event) => setDraftName(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="imported-item-quantity">Quantity</label>

            <input
              id="imported-item-quantity"
              type="number"
              min="0.01"
              step="0.01"
              value={draftQuantity}
              onChange={(event) => setDraftQuantity(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="imported-item-unit">Unit</label>

            <select
              id="imported-item-unit"
              value={draftUnit}
              onChange={(event) => setDraftUnit(event.target.value)}
            >
              <option value="each">Each</option>
              <option value="pack">Pack</option>
              <option value="lb">Pound</option>
              <option value="oz">Ounce</option>
              <option value="gallon">Gallon</option>
              <option value="liter">Liter</option>
              <option value="kg">Kilogram</option>
              <option value="g">Gram</option>
            </select>
          </div>

          <div>
            <label htmlFor="imported-item-price">Unit price</label>

            <input
              id="imported-item-price"
              type="number"
              min="0.01"
              step="0.01"
              placeholder="0.50"
              value={draftPrice}
              onChange={(event) => setDraftPrice(event.target.value)}
            />
          </div>

          <div className="imported-item-editor-actions">
            <button
              className="save-imported-item-button"
              type="button"
              onClick={saveDraftItem}
            >
              {editorMode === "add" ? "Add Item" : "Save Item"}
            </button>

            <button
              className="cancel-imported-item-button"
              type="button"
              onClick={resetEditor}
            >
              Cancel
            </button>
          </div>

          {editorError && (
            <p className="imported-item-editor-error">{editorError}</p>
          )}
        </div>
      )}

      {items.length === 0 ? (
        <p className="imported-items-empty">
          No items were detected. Add the receipt items manually before saving.
        </p>
      ) : (
        <div className="imported-items-list">
          {items.map((item, itemIndex) => {
            const rowTotalCents = Math.round(
              Number(item.quantity) * Number(item.unit_price_cents),
            );

            return (
              <div
                className="imported-item-row"
                key={`${item.name}-${itemIndex}`}
              >
                <div className="imported-item-details">
                  <strong>{item.name}</strong>

                  <span>
                    {item.quantity} {item.unit} ×{" "}
                    {formatMoney(item.unit_price_cents)}
                  </span>
                </div>

                <strong className="imported-item-total">
                  {formatMoney(rowTotalCents)}
                </strong>

                <div className="imported-item-actions">
                  <button
                    className="edit-imported-item-button"
                    type="button"
                    onClick={() => startEditingItem(item, itemIndex)}
                  >
                    Edit
                  </button>

                  <button
                    className="delete-imported-item-button"
                    type="button"
                    onClick={() => deleteItem(itemIndex)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default ImportedItemsReview;
