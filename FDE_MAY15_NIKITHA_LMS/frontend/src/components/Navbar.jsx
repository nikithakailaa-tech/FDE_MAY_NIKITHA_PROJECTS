import { Link, useLocation } from "react-router-dom";

const NAV_LINKS = [
  { to: "/", label: "Dashboard" },
  { to: "/books", label: "Books" },
  { to: "/borrowers", label: "Borrowers" },
  { to: "/transactions", label: "Borrow / Return" },
  { to: "/search", label: "Search" },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="navbar-icon">📚</span>
        <span>Library MS</span>
      </div>
      <ul className="navbar-links">
        {NAV_LINKS.map((link) => (
          <li key={link.to}>
            <Link
              to={link.to}
              className={pathname === link.to ? "active" : ""}
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
