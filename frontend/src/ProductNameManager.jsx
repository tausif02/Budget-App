// ProductNameManager.jsx
import { useCallback, useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

function ProductNameManager({
  isOpen,
  onClose,
  onAliasesChanged,
  availableNames,
}) {
  const [aliases, setAliases] = useState([]);
  const [rawName, setRawName] = useState("");
  const [canonicalName, setCanonicalName] = useState("");
  const [editingAliasId, setEditingAliasId] = useState(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadAliases = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/items/name-aliases`);

      if (!response.ok) {
        throw new Error("Failed to load product names.");
      }

      const data = await response.json();
      setAliases(data);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadAliases();
    }
  }, [isOpen, loadAliases]);

  function resetForm() {
    setRawName("");
    setCanonicalName("");
    setEditingAliasId(null);
    setErrorMessage("");
  }

  function closeManager() {
    resetForm();
    onClose();
  }

  function startEditingAlias(alias) {
    setRawName(alias.raw_name);
    setCanonicalName(alias.canonical_name);
    setEditingAliasId(alias.id);
    setErrorMessage("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const cleanedRawName = rawName.trim();
    const cleanedCanonicalName = canonicalName.trim();

    if (!cleanedRawName || !cleanedCanonicalName) {
      setErrorMessage(
        "Enter both the receipt name and the clean product name.",
      );
      return;
    }

    setIsSaving(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/items/name-aliases`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          raw_name: cleanedRawName,
          canonical_name: cleanedCanonicalName,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to save the product name.",
        );
      }

      resetForm();
      await loadAliases();

      if (onAliasesChanged) {
        await onAliasesChanged();
      }
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteAlias(alias) {
    const confirmed = window.confirm(
      `Remove the clean name for "${alias.raw_name}"?`,
    );

    if (!confirmed) {
      return;
    }

    setErrorMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/items/name-aliases/${alias.id}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to remove the product name.",
        );
      }

      if (editingAliasId === alias.id) {
        resetForm();
      }

      await loadAliases();

      if (onAliasesChanged) {
        await onAliasesChanged();
      }
    } catch (error) {
      setErrorMessage(error.message);
    }
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="modal-overlay product-name-overlay"
      onMouseDown={closeManager}
    >
      <section
        className="expense-modal product-name-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="product-name-manager-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <p>Product cleanup</p>

            <h2 id="product-name-manager-title">Manage Product Names</h2>
          </div>

          <button
            className="modal-close"
            type="button"
            aria-label="Close product-name manager"
            onClick={closeManager}
          >
            ×
          </button>
        </div>

        <p className="product-name-description">
          Connect abbreviated receipt text to a clean product name. The original
          receipt item will remain unchanged.
        </p>

        <form className="product-name-form" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="raw-product-name">Receipt name</label>

            <input
              id="raw-product-name"
              type="text"
              list="tracked-product-names"
              required
              disabled={editingAliasId !== null}
              placeholder="GV ONION PW"
              value={rawName}
              onChange={(event) => setRawName(event.target.value)}
            />

            <datalist id="tracked-product-names">
              {availableNames.map((name) => (
                <option value={name} key={name} />
              ))}
            </datalist>
          </div>

          <div>
            <label htmlFor="canonical-product-name">Display as</label>

            <input
              id="canonical-product-name"
              type="text"
              required
              placeholder="Great Value Onion Powder"
              value={canonicalName}
              onChange={(event) => setCanonicalName(event.target.value)}
            />
          </div>

          <div className="product-name-form-actions">
            <button
              className="save-product-name-button"
              type="submit"
              disabled={isSaving}
            >
              {isSaving
                ? "Saving..."
                : editingAliasId === null
                  ? "Save Product Name"
                  : "Update Product Name"}
            </button>

            {editingAliasId !== null && (
              <button
                className="cancel-product-name-button"
                type="button"
                onClick={resetForm}
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        {errorMessage && <p className="product-name-error">{errorMessage}</p>}

        <div className="saved-product-names">
          <div className="saved-product-names-header">
            <h3>Saved product names</h3>
            <span>{aliases.length}</span>
          </div>

          {isLoading ? (
            <p className="product-name-message">Loading saved names...</p>
          ) : aliases.length === 0 ? (
            <p className="product-name-message">
              No clean product names have been saved yet.
            </p>
          ) : (
            <div className="product-name-list">
              {aliases.map((alias) => (
                <div className="product-name-row" key={alias.id}>
                  <div>
                    <span>{alias.raw_name}</span>
                    <strong>{alias.canonical_name}</strong>
                  </div>

                  <div className="product-name-row-actions">
                    <button
                      className="edit-product-name-button"
                      type="button"
                      onClick={() => startEditingAlias(alias)}
                    >
                      Edit
                    </button>

                    <button
                      className="delete-product-name-button"
                      type="button"
                      onClick={() => handleDeleteAlias(alias)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default ProductNameManager;
