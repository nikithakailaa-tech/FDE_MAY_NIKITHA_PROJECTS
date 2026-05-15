import { useEffect, useState } from "react";
import { transactionService } from "../services/transactionService";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    transactionService
      .getDashboard()
      .then((res) => setStats(res.data))
      .catch(() => setError("Failed to load dashboard data."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-center">Loading dashboard…</div>;
  if (error) return <div className="page-center error">{error}</div>;

  const statCards = [
    { label: "Total Books", value: stats.total_books, color: "blue" },
    { label: "Available", value: stats.available_books, color: "green" },
    { label: "Borrowed", value: stats.borrowed_books, color: "orange" },
    { label: "Borrowers", value: stats.total_borrowers, color: "purple" },
  ];

  return (
    <div className="page">
      <h1 className="page-title">Dashboard</h1>
      <div className="stat-grid">
        {statCards.map((card) => (
          <div key={card.label} className={`stat-card stat-card--${card.color}`}>
            <div className="stat-value">{card.value}</div>
            <div className="stat-label">{card.label}</div>
          </div>
        ))}
      </div>

      <h2 className="section-title">Recent Transactions</h2>
      {stats.recent_transactions.length === 0 ? (
        <p className="empty-msg">No transactions yet.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Book</th>
              <th>Borrower</th>
              <th>Borrow Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_transactions.map((tx) => (
              <tr key={tx.transaction_id}>
                <td>{tx.transaction_id}</td>
                <td>{tx.book?.title ?? tx.book_id}</td>
                <td>{tx.borrower?.borrower_name ?? tx.borrower_id}</td>
                <td>{new Date(tx.borrow_date).toLocaleDateString()}</td>
                <td>
                  <span className={`badge ${tx.return_date ? "badge--green" : "badge--orange"}`}>
                    {tx.return_date ? "Returned" : "Active"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
