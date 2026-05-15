import api from "../api";

export const borrowerService = {
  getAll: () => api.get("/borrowers/"),
  create: (data) => api.post("/borrowers/", data),
  update: (id, data) => api.put(`/borrowers/${id}`, data),
  delete: (id) => api.delete(`/borrowers/${id}`),
};
