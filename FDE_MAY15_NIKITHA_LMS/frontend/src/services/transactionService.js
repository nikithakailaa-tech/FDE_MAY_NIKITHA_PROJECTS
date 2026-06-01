import api from "../api";

export const transactionService = {
  getAll: () => api.get("/transactions"),
  borrow: (data) => api.post("/borrow", data),
  return: (data) => api.post("/return", data),
  getDashboard: () => api.get("/dashboard"),
};
