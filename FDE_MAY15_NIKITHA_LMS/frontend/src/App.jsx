import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Books from "./pages/Books";
import Borrowers from "./pages/Borrowers";
import Transactions from "./pages/Transactions";
import Search from "./pages/Search";
import "./index.css";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/books" element={<Books />} />
          <Route path="/borrowers" element={<Borrowers />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
