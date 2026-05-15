import { useState } from "react";
import { bookService } from "../services/bookService";

export default function Search() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [author, setAuthor] = useState("");
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const params = {};
      if (query) params.q = query;
      if (category) params.category = category;
      if (author) params.author = author;
      const res = await bookService.search(params);
      setResults(res.data);
      setSearched(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery(""); setCategory(""); setAuthor(""); setResults([]); setSearched(false);
  };

  return (
    <div className="page">
      <h1 className="page-title">Search Books</h1>

      <form className="form-card" onSubmit={handleSearch}>
        <div className="form-grid">
          <div className="form-group">
            <label>Keyword (title / author / category / ISBN)</label>
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. Python, Tolkien…" />
          </div>
          <div className="form-group">
            <label>Filter by Category</label>
            <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Fiction" />
          </div>
          <div className="form-group">
            <label>Filter by Author</label>
            <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="e.g. George Orwell" />
          </div>
        </div>
        <div className="btn-row">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Searching…" : "Search"}
          </button>
          <button type="button" className="btn btn-secondary" onClick={handleClear}>Clear</button>
        </div>
      </form>

      {searched && (
        <>
          <p className="result-count">{results.length} result{results.length !== 1 ? "s" : ""} found</p>
          <table className="table">
            <thead>
              <tr><th>ID</th><th>Title</th><th>Author</th><th>Category</th><th>ISBN</th><th>Status</th></tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr><td colSpan={6} className="empty-cell">No books matched your search.</td></tr>
              ) : results.map((b) => (
                <tr key={b.book_id}>
                  <td>{b.book_id}</td>
                  <td>{b.title}</td>
                  <td>{b.author}</td>
                  <td>{b.category}</td>
                  <td>{b.isbn}</td>
                  <td><span className={`badge ${b.availability_status === "available" ? "badge--green" : "badge--orange"}`}>{b.availability_status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
