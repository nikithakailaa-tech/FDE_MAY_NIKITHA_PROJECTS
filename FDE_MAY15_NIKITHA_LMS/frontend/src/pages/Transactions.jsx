import { useEffect, useState } from "react";
import { transactionService } from "../services/transactionService";
import { bookService } from "../services/bookService";
import { borrowerService } from "../services/borrowerService";

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [books, setBooks] = useState([]);
  const [borrowers, setBorrowers] = useState([]);
  const [borrowForm, setBorrowForm] = useState({ book_id: "", borrower_id: "" });
  const [returnId, setReturnId] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () => {
    transactionService.getAll().then((r) => setTransactions(r.data));
    bookService.getAll().then((r) => setBooks(r.data));
    borrowerService.getAll().then((r) => setBorrowers(r.data));
  };

  useEffect(() => { load(); }, []);

  const flash = (msg, isError = false) => {
    if (isError) { setError(msg); setTimeout(() => setError(""), 4000); }
    else { setSuccess(msg); setTimeout(() => setSuccess(""), 4000); }
  };

  const handleBorrow = async (e) => {
    e.preventDefault();
    try {
      await transactionService.borrow({ book_id: Number(borrowForm.book_id), borrower_id: Number(borrowForm.borrower_id) });
      flash("Book borrowed successfully!"); setBorrowForm({ book_id: "", borrower_id: "" }); load();
    } catch (err) { flash(err.response?.data?.detail || "Borrow failed.", true); }
  };

  const handleReturn = async (e) => {
    e.preventDefault();
    try {
      await transactionService.return({ transaction_id: Number(returnId) });
      flash("Book returned successfully!"); setReturnId(""); load();
    } catch (err) { flash(err.response?.data?.detail || "Return failed.", true); }
  };

  const availableBooks = books.filter((b) => b.availability_status === "available");
  const activeTransactions = transactions.filter((t) => !t.return_date);

  return (
    <div className="page">
      <h1 className="page-title">Borrow / Return</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="two-col">
        {/* Borrow */}
        <form className="form-card" onSubmit={handleBorrow}>
          <h2>📖 Borrow a Book</h2>
          <div className="form-group">
            <label>Select Book (Available)</label>
            <select required value={borrowForm.book_id} onChange={(e) => setBorrowForm({ ...borrowForm, book_id: e.target.value })}>
              <option value="">-- Choose book --</option>
              {availableBooks.map((b) => (
                <option key={b.book_id} value={b.book_id}>{b.title} ({b.author})</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Select Borrower</label>
            <select required value={borrowForm.borrower_id} onChange={(e) => setBorrowForm({ ...borrowForm, borrower_id: e.target.value })}>
              <option value="">-- Choose borrower --</option>
              {borrowers.map((b) => (
                <option key={b.borrower_id} value={b.borrower_id}>{b.borrower_name} ({b.email})</option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary">Borrow Book</button>
        </form>

        {/* Return */}
        <form className="form-card" onSubmit={handleReturn}>
          <h2>↩️ Return a Book</h2>
          <div className="form-group">
            <label>Select Active Transaction</label>
            <select required value={returnId} onChange={(e) => setReturnId(e.target.value)}>
              <option value="">-- Choose transaction --</option>
              {activeTransactions.map((t) => (
                <option key={t.transaction_id} value={t.transaction_id}>
                  #{t.transaction_id} — {t.book?.title ?? `Book #${t.book_id}`} → {t.borrower?.borrower_name ?? `Borrower #${t.borrower_id}`}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary">Return Book</button>
        </form>
      </div>

      <h2 className="section-title">All Transactions</h2>
      <table className="table">
        <thead>
          <tr><th>#</th><th>Book</th><th>Borrower</th><th>Borrow Date</th><th>Return Date</th><th>Status</th></tr>
        </thead>
        <tbody>
          {transactions.length === 0 ? (
            <tr><td colSpan={6} className="empty-cell">No transactions yet.</td></tr>
          ) : transactions.map((t) => (
            <tr key={t.transaction_id}>
              <td>{t.transaction_id}</td>
              <td>{t.book?.title ?? t.book_id}</td>
              <td>{t.borrower?.borrower_name ?? t.borrower_id}</td>
              <td>{new Date(t.borrow_date).toLocaleDateString()}</td>
              <td>{t.return_date ? new Date(t.return_date).toLocaleDateString() : "—"}</td>
              <td><span className={`badge ${t.return_date ? "badge--green" : "badge--orange"}`}>{t.return_date ? "Returned" : "Active"}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
