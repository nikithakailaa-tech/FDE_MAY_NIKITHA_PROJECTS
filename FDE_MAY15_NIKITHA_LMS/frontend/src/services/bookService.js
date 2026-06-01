import api from "../api";

export const bookService = {
  getAll: () => api.get("/books/"),
  getById: (id) => api.get(`/books/${id}`),
  create: (data) => api.post("/books/", data),
  update: (id, data) => api.put(`/books/${id}`, data),
  delete: (id) => api.delete(`/books/${id}`),
  search: (params) => api.get("/search", { params }),
};
