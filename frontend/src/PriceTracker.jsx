// PriceTracker.jsx
import { useCallback, useEffect, useState } from "react";
import ProductNameManager from "./ProductNameManager";

const API_BASE_URL = "http://127.0.0.1:8000";

function formatDate(dateString) {
  const [year, month, day] = dateString.split("-").map(Number);
  const localDate = new Date(year, month - 1, day);

  return localDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatMoney(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

function PriceTracker() {
  const [priceSummaries, setPriceSummaries] = useState([]);
  const [priceSearch, setPriceSearch] = useState("");
  const [isLoadingSummaries, setIsLoadingSummaries] = useState(true);
  const [summariesError, setSummariesError] = useState("");

  const [selectedProduct, setSelectedProduct] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [isNameManagerOpen, setIsNameManagerOpen] = useState(false);

  const loadPriceSummaries = useCallback(async () => {
    setIsLoadingSummaries(true);
    setSummariesError("");

    try {
      const response = await fetch(`${API_BASE_URL}/items/price-summaries`);

      if (!response.ok) {
        throw new Error("Failed to load tracked prices.");
      }

      const data = await response.json();
      setPriceSummaries(data);
    } catch (error) {
      setSummariesError(error.message);
    } finally {
      setIsLoadingSummaries(false);
    }
  }, []);

  useEffect(() => {
    loadPriceSummaries();
  }, [loadPriceSummaries]);

  async function openPriceHistory(summary) {
    setSelectedProduct(summary);
    setPriceHistory([]);
    setHistoryError("");
    setIsLoadingHistory(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/items/price-history?name=${encodeURIComponent(
          summary.name,
        )}`,
      );

      if (!response.ok) {
        throw new Error("Failed to load price history.");
      }

      const data = await response.json();

      const matchingUnitHistory = data.filter(
        (entry) =>
          entry.unit.trim().toLowerCase() === summary.unit.trim().toLowerCase(),
      );

      setPriceHistory(matchingUnitHistory);
    } catch (error) {
      setHistoryError(error.message);
    } finally {
      setIsLoadingHistory(false);
    }
  }

  function closePriceHistory() {
    setSelectedProduct(null);
    setPriceHistory([]);
    setHistoryError("");
  }

  const normalizedSearch = priceSearch.trim().toLowerCase();

  const filteredPriceSummaries = priceSummaries.filter((summary) => {
    if (!normalizedSearch) {
      return true;
    }

    const searchableText = [
      summary.name,
      summary.unit,
      summary.latest_merchant || "",
    ]
      .join(" ")
      .toLowerCase();

    return searchableText.includes(normalizedSearch);
  });

  const repeatedProductCount = priceSummaries.filter(
    (summary) => summary.purchase_count > 1,
  ).length;

  const increasedPriceCount = priceSummaries.filter(
    (summary) => summary.price_change_cents > 0,
  ).length;

  const decreasedPriceCount = priceSummaries.filter(
    (summary) => summary.price_change_cents < 0,
  ).length;

  const latestHistoryEntry = priceHistory[0] ?? null;
  const previousHistoryEntry = priceHistory[1] ?? null;

  const canCompareHistory =
    latestHistoryEntry !== null && previousHistoryEntry !== null;

  const historyChangeCents = canCompareHistory
    ? latestHistoryEntry.unit_price_cents -
      previousHistoryEntry.unit_price_cents
    : 0;

  const historyChangePercent =
    canCompareHistory && previousHistoryEntry.unit_price_cents > 0
      ? (historyChangeCents / previousHistoryEntry.unit_price_cents) * 100
      : 0;

  const availableProductNames = [
    ...new Set(priceSummaries.map((summary) => summary.name)),
  ].sort((firstName, secondName) => firstName.localeCompare(secondName));

  return (
    <>
      <section className="price-tracker-section" id="price-tracker">
        <div className="price-tracker-header">
          <div>
            <p className="section-eyebrow">Purchase intelligence</p>
            <h2>Price Tracker</h2>
            <p>
              Monitor repeated purchases and see when everyday prices change.
            </p>
          </div>

          <div className="price-tracker-controls">
            <label className="price-search" htmlFor="price-search-input">
              <span>Search products</span>

              <input
                id="price-search-input"
                type="search"
                placeholder="Milk, Walmart, gallon..."
                value={priceSearch}
                onChange={(event) => setPriceSearch(event.target.value)}
              />
            </label>

            <button
              className="refresh-prices-button manage-product-names-button"
              type="button"
              onClick={() => setIsNameManagerOpen(true)}
            >
              Manage Names
            </button>

            <button
              className="refresh-prices-button"
              type="button"
              disabled={isLoadingSummaries}
              onClick={loadPriceSummaries}
            >
              {isLoadingSummaries ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        <div className="price-tracker-stats">
          <div>
            <span>Tracked products</span>
            <strong>{priceSummaries.length}</strong>
          </div>

          <div>
            <span>Repeated purchases</span>
            <strong>{repeatedProductCount}</strong>
          </div>

          <div>
            <span>Prices increased</span>
            <strong>{increasedPriceCount}</strong>
          </div>

          <div>
            <span>Prices decreased</span>
            <strong>{decreasedPriceCount}</strong>
          </div>
        </div>

        {isLoadingSummaries ? (
          <p className="price-tracker-message">Loading tracked prices...</p>
        ) : summariesError ? (
          <div className="price-tracker-error">
            <p>{summariesError}</p>

            <button type="button" onClick={loadPriceSummaries}>
              Try Again
            </button>
          </div>
        ) : filteredPriceSummaries.length === 0 ? (
          <p className="price-tracker-message">
            {priceSearch
              ? "No tracked products match your search."
              : "Add receipt items to begin tracking their prices."}
          </p>
        ) : (
          <div className="price-tracker-grid">
            {filteredPriceSummaries.map((summary) => {
              const hasPriceChange = summary.price_change_cents !== null;

              const priceIncreased = summary.price_change_cents > 0;

              const priceDecreased = summary.price_change_cents < 0;

              const changeClass = !hasPriceChange
                ? "price-first-purchase"
                : priceIncreased
                  ? "price-went-up"
                  : priceDecreased
                    ? "price-went-down"
                    : "price-stayed-same";

              return (
                <button
                  className={`price-tracker-card ${changeClass}`}
                  type="button"
                  key={`${summary.name}-${summary.unit}`}
                  onClick={() => openPriceHistory(summary)}
                >
                  <div className="price-card-heading">
                    <div>
                      <span className="price-card-unit">{summary.unit}</span>

                      <h3>{summary.name}</h3>
                    </div>

                    <span className="price-card-count">
                      {summary.purchase_count}{" "}
                      {summary.purchase_count === 1 ? "purchase" : "purchases"}
                    </span>
                  </div>

                  <div className="price-card-value">
                    <span>Latest unit price</span>

                    <strong>
                      {formatMoney(summary.latest_unit_price_cents)}
                    </strong>
                  </div>

                  <div className="price-card-change">
                    {!hasPriceChange ? (
                      <span>First recorded purchase</span>
                    ) : summary.price_change_cents === 0 ? (
                      <span>No change from previous purchase</span>
                    ) : (
                      <span>
                        {priceIncreased ? "↑" : "↓"}{" "}
                        {priceIncreased ? "+" : "-"}
                        {formatMoney(Math.abs(summary.price_change_cents))} (
                        {priceIncreased ? "+" : "-"}
                        {Math.abs(summary.price_change_percent).toFixed(1)}
                        %)
                      </span>
                    )}
                  </div>

                  <div className="price-card-footer">
                    <span>{summary.latest_merchant || "Unknown Merchant"}</span>

                    <span>{formatDate(summary.latest_purchase_date)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>
      <ProductNameManager
        isOpen={isNameManagerOpen}
        onClose={() => setIsNameManagerOpen(false)}
        onAliasesChanged={loadPriceSummaries}
        availableNames={availableProductNames}
      />

      {selectedProduct && (
        <div
          className="modal-overlay price-history-overlay"
          onMouseDown={closePriceHistory}
        >
          <section
            className="expense-modal price-history-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="tracker-history-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <p>Price tracking</p>

                <h2 id="tracker-history-title">
                  {selectedProduct.name} history
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

            {canCompareHistory && (
              <div
                className={`price-change-summary ${
                  historyChangeCents > 0
                    ? "price-increase"
                    : historyChangeCents < 0
                      ? "price-decrease"
                      : "price-unchanged"
                }`}
              >
                <span>Since previous purchase</span>

                <strong>
                  {historyChangeCents === 0 ? (
                    "No price change"
                  ) : (
                    <>
                      {historyChangeCents > 0 ? "↑" : "↓"}{" "}
                      {formatMoney(Math.abs(historyChangeCents))} (
                      {historyChangeCents > 0 ? "+" : "-"}
                      {Math.abs(historyChangePercent).toFixed(1)}
                      %)
                    </>
                  )}
                </strong>
              </div>
            )}

            {isLoadingHistory ? (
              <p className="items-message">Loading price history...</p>
            ) : historyError ? (
              <p className="items-message">{historyError}</p>
            ) : priceHistory.length === 0 ? (
              <p className="items-message">
                No purchases found for this product and unit.
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
                      <strong>{formatMoney(entry.unit_price_cents)}</strong>

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
    </>
  );
}

export default PriceTracker;
