import { useEffect, useState } from "react";
import { borrowerService } from "../services/borrowerService";

const EMPTY = { borrower_name: "", email: "", phone: "" };

export default function Borrowers() {
  const [borrowers, setBorrowers] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [editId, setEditId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () => borrowerService.getAll().then((r) => setBorrowers(r.data));

  useEffect(() => { load(); }, []);

  const flash = (msg, isError = false) => {
    if (isError) { setError(msg); setTimeout(() => setError(""), 3000); }
    else { setSuccess(msg); setTimeout(() => setSuccess(""), 3000); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await borrowerService.update(editId, form);
        flash("Borrower updated.");
      } else {
        await borrowerService.create(form);
        flash("Borrower added.");
      }
      setForm(EMPTY); setEditId(null); setShowForm(false); load();
    } catch (err) {
      flash(err.response?.data?.detail || "Operation failed.", true);
    }
  };

  const handleEdit = (b) => {
    setForm({ borrower_name: b.borrower_name, email: b.email, phone: b.phone });
    setEditId(b.borrower_id); setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this borrower?")) return;
    try { await borrowerService.delete(id); flash("Deleted."); load(); }
    catch { flash("Delete failed.", true); }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Borrower Management</h1>
        <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); setForm(EMPTY); setEditId(null); }}>
          {showForm ? "Cancel" : "+ Add Borrower"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {showForm && (
        <form className="form-card" onSubmit={handleSubmit}>
          <h2>{editId ? "Edit Borrower" : "Add Borrower"}</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Name</label>
              <input required value={form.borrower_name} onChange={(e) => setForm({ ...form, borrower_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
          </div>
          <button type="submit" className="btn btn-primary">{editId ? "Update" : "Add"} Borrower</button>
        </form>
      )}

      <table className="table">
        <thead>
          <tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {borrowers.length === 0 ? (
            <tr><td colSpan={5} className="empty-cell">No borrowers found.</td></tr>
          ) : borrowers.map((b) => (
            <tr key={b.borrower_id}>
              <td>{b.borrower_id}</td>
              <td>{b.borrower_name}</td>
              <td>{b.email}</td>
              <td>{b.phone}</td>
              <td className="action-cell">
                <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(b)}>Edit</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(b.borrower_id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
