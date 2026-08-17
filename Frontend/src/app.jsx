import { useState } from "react";

function App() {
  const [url, setUrl] = useState("");
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzeBook = async () => {
    if (!url.trim()) {
      setError("Please enter a book URL.");
      return;
    }

    setLoading(true);
    setError("");
    setBook(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail?.message || "Failed to analyze the book."
        );
      }

      setBook(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <h1>BookGuard</h1>
      <p>Check a book before you buy.</p>

      <input
        type="url"
        placeholder="Paste a book URL..."
        value={url}
        onChange={(event) => setUrl(event.target.value)}
      />

      <button onClick={analyzeBook} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Book"}
      </button>

      {error && <p>{error}</p>}

      {book && (
        <section>
          <h2>{book.book_title}</h2>

          <p>
            <strong>Author:</strong> {book.author}
          </p>

          <p>
            <strong>ISBN-13:</strong> {book.isbn_13}
          </p>

          <p>
            <strong>ISBN-10:</strong> {book.isbn_10}
          </p>

          <p>
            <strong>Publisher:</strong> {book.publisher}
          </p>

          <p>
            <strong>Edition:</strong> {book.edition}
          </p>

          <p>
            <strong>Price:</strong> {book.price?.symbol}
            {book.price?.value}
          </p>

          <p>
            <strong>Availability:</strong> {book.availability}
          </p>

          <p>
            <strong>Store:</strong> {book.store}
          </p>

          <p>
            <strong>Seller:</strong> {book.seller_name}
          </p>
        </section>
      )}
    </main>
  );
}

export default App;