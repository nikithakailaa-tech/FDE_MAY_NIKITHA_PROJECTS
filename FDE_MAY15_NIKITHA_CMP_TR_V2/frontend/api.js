const API_URL = "http://127.0.0.1:8000";

// Get token from localStorage
function getToken() {
    return localStorage.getItem("token");
}

// Save token to localStorage
function saveToken(token) {
    localStorage.setItem("token", token);
}

// Remove token (logout)
function removeToken() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
}

// Headers with token
function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
    };
}

// REGISTER
async function registerUser(name, email, password, role) {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role })
    });
    return res.json();
}

// LOGIN
async function loginUser(email, password) {
    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    return res.json();
}

// GET DASHBOARD STATS
async function getDashboardStats() {
    const res = await fetch(`${API_URL}/dashboard/stats`, {
        headers: authHeaders()
    });
    return res.json();
}

// GET ALL COMPLAINTS
async function getComplaints() {
    const res = await fetch(`${API_URL}/complaints/`, {
        headers: authHeaders()
    });
    return res.json();
}

// CREATE COMPLAINT
async function createComplaint(title, description, category_id, priority) {
    const res = await fetch(`${API_URL}/complaints/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title, description, category_id, priority })
    });
    return res.json();
}

// UPDATE COMPLAINT
async function updateComplaint(id, data) {
    const res = await fetch(`${API_URL}/complaints/${id}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return res.json();
}

// GET CATEGORIES
async function getCategories() {
    const res = await fetch(`${API_URL}/categories/`, {
        headers: authHeaders()
    });
    return res.json();
}

// SUBMIT FEEDBACK
async function submitFeedback(complaint_id, rating, comments) {
    const res = await fetch(`${API_URL}/feedback/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ complaint_id, rating, comments })
    });
    return res.json();
}

// CHECK IF LOGGED IN
function isLoggedIn() {
    return !!getToken();
}

// REDIRECT IF NOT LOGGED IN
function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = "index.html";
    }
}

// LOGOUT
function logout() {
    removeToken();
    window.location.href = "index.html";
}