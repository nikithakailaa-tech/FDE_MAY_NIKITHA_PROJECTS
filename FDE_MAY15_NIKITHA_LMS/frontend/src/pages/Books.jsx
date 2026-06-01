import { useEffect, useState } from "react";
import { bookService } from "../services/bookService";

const EMPTY_FORM = { title: "", author: "", category: "", isbn: "", availability_status: "available" };

export default function Books() {
  const [books, setBooks] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () => bookService.getAll().then((r) => setBooks(r.data));

  useEffect(() => { load(); }, []);

  const flash = (msg, isError = false) => {
    if (isError) { setError(msg); setTimeout(() => setError(""), 3000); }
    else { setSuccess(msg); setTimeout(() => setSuccess(""), 3000); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await bookService.update(editId, form);
        flash("Book updated successfully.");
      } else {
        await bookService.create(form);
        flash("Book added successfully.");
      }
      setForm(EMPTY_FORM); setEditId(null); setShowForm(false); load();
    } catch (err) {
      flash(err.response?.data?.detail || "Operation failed.", true);
    }
  };

  const handleEdit = (book) => {
    setForm({ title: book.title, author: book.author, category: book.category, isbn: book.isbn, availability_status: book.availability_status });
    setEditId(book.book_id); setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this book?")) return;
    try {
      await bookService.delete(id);
      flash("Book deleted."); load();
    } catch { flash("Delete failed.", true); }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Book Management</h1>
        <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); setForm(EMPTY_FORM); setEditId(null); }}>
          {showForm ? "Cancel" : "+ Add Book"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {showForm && (
        <form className="form-card" onSubmit={handleSubmit}>
          <h2>{editId ? "Edit Book" : "Add New Book"}</h2>
          <div className="form-grid">
            {["title", "author", "category", "isbn"].map((field) => (
              <div className="form-group" key={field}>
                <label>{field.charAt(0).toUpperCase() + field.slice(1)}</label>
                <input required value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} />
              </div>
            ))}
            <div className="form-group">
              <label>Status</label>
              <select value={form.availability_status} onChange={(e) => setForm({ ...form, availability_status: e.target.value })}>
                <option value="available">Available</option>
                <option value="borrowed">Borrowed</option>
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary">{editId ? "Update" : "Add"} Book</button>
        </form>
      )}

      <table className="table">
        <thead>
          <tr><th>ID</th><th>Title</th><th>Author</th><th>Category</th><th>ISBN</th><th>Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {books.length === 0 ? (
            <tr><td colSpan={7} className="empty-cell">No books found.</td></tr>
          ) : books.map((b) => (
            <tr key={b.book_id}>
              <td>{b.book_id}</td>
              <td>{b.title}</td>
              <td>{b.author}</td>
              <td>{b.category}</td>
              <td>{b.isbn}</td>
              <td><span className={`badge ${b.availability_status === "available" ? "badge--green" : "badge--orange"}`}>{b.availability_status}</span></td>
              <td className="action-cell">
                <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(b)}>Edit</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(b.book_id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
