const API_URL = "http://127.0.0.1:8002";

function getToken() { return localStorage.getItem("token"); }
function saveToken(token) { localStorage.setItem("token", token); }
function removeToken() { localStorage.removeItem("token"); localStorage.removeItem("user"); }
function isLoggedIn() { return !!getToken(); }

function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
    };
}

function requireAuth() {
    if (!isLoggedIn()) window.location.href = "/";
}

function logout() {
    removeToken();
    window.location.href = "/";
}

// AUTH
async function registerUser(name, email, password, role) {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role })
    });
    return res.json();
}

async function loginUser(email, password) {
    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    return res.json();
}

async function getMe() {
    const res = await fetch(`${API_URL}/auth/me`, { headers: authHeaders() });
    if (res.status === 401) {
        removeToken();
        window.location.href = "/";
        return null;
    }
    return res.json();
}

async function getAllUsers() {
    const res = await fetch(`${API_URL}/auth/users`, { headers: authHeaders() });
    return res.json();
}

async function toggleUserActive(userId) {
    const res = await fetch(`${API_URL}/auth/users/${userId}/toggle-active`, {
        method: "PUT", headers: authHeaders()
    });
    return res.json();
}

async function updateUserRole(userId, role) {
    const res = await fetch(`${API_URL}/auth/users/${userId}/role`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({ role })
    });
    return res.json();
}

// COMPLAINTS
async function getComplaints() {
    const res = await fetch(`${API_URL}/complaints/`, { headers: authHeaders() });
    return res.json();
}

async function getComplaint(id) {
    const res = await fetch(`${API_URL}/complaints/${id}`, { headers: authHeaders() });
    return res.json();
}

async function createComplaint(title, description, category_id, priority) {
    const res = await fetch(`${API_URL}/complaints/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title, description, category_id, priority })
    });
    return res.json();
}

async function updateComplaint(id, data) {
    const res = await fetch(`${API_URL}/complaints/${id}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return res.json();
}

async function getComplaintHistory(id) {
    const res = await fetch(`${API_URL}/complaints/${id}/history`, { headers: authHeaders() });
    return res.json();
}

// CATEGORIES
async function getCategories() {
    const res = await fetch(`${API_URL}/categories/`, { headers: authHeaders() });
    return res.json();
}

async function createCategory(name, description) {
    const res = await fetch(`${API_URL}/categories/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ name, description })
    });
    return res.json();
}

async function deleteCategory(id) {
    const res = await fetch(`${API_URL}/categories/${id}`, {
        method: "DELETE", headers: authHeaders()
    });
    return res.json();
}

// DASHBOARD
async function getDashboardStats() {
    const res = await fetch(`${API_URL}/dashboard/stats`, { headers: authHeaders() });
    return res.json();
}

async function getCategoryStats() {
    const res = await fetch(`${API_URL}/dashboard/category-stats`, { headers: authHeaders() });
    return res.json();
}

async function getAgentStats() {
    const res = await fetch(`${API_URL}/dashboard/agent-stats`, { headers: authHeaders() });
    return res.json();
}

async function getMonthlyTrends() {
    const res = await fetch(`${API_URL}/dashboard/monthly-trends`, { headers: authHeaders() });
    return res.json();
}

// FEEDBACK
async function getMyFeedback() {
    const res = await fetch(`${API_URL}/feedback/`, { headers: authHeaders() });
    return res.json();
}

async function submitFeedback(complaint_id, rating, comments) {
    const res = await fetch(`${API_URL}/feedback/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ complaint_id, rating, comments })
    });
    return res.json();
}

// NOTIFICATIONS
async function getNotifications() {
    const res = await fetch(`${API_URL}/notifications/`, { headers: authHeaders() });
    return res.json();
}

async function getUnreadCount() {
    const res = await fetch(`${API_URL}/notifications/unread-count`, { headers: authHeaders() });
    return res.json();
}

async function markNotificationRead(id) {
    const res = await fetch(`${API_URL}/notifications/${id}/read`, {
        method: "PUT", headers: authHeaders()
    });
    return res.json();
}

async function markAllNotificationsRead() {
    const res = await fetch(`${API_URL}/notifications/read-all/mark`, {
        method: "PUT", headers: authHeaders()
    });
    return res.json();
}

// NOTIFICATION BELL — load unread count into navbar badge
async function loadNotificationBadge() {
    try {
        const data = await getUnreadCount();
        const badge = document.getElementById("notif-badge");
        if (badge) {
            badge.textContent = data.count || "";
            badge.style.display = data.count > 0 ? "inline-block" : "none";
        }
    } catch (e) {}
}

async function toggleNotificationDropdown() {
    const panel = document.getElementById("notif-panel");
    if (!panel) return;
    if (panel.style.display === "block") {
        panel.style.display = "none";
        return;
    }
    panel.style.display = "block";
    panel.innerHTML = `<div style="padding:12px;color:#666;font-size:13px;">Loading...</div>`;
    const notifications = await getNotifications();
    if (!notifications.length) {
        panel.innerHTML = `<div style="padding:16px;color:#666;font-size:13px;text-align:center;">No notifications</div>`;
        return;
    }
    panel.innerHTML = `
        <div class="notif-header">
            <span>Notifications</span>
            <button onclick="markAllRead()" style="font-size:12px;background:none;border:none;color:#1a73e8;cursor:pointer;">Mark all read</button>
        </div>
        ${notifications.map(n => `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="markOneRead(${n.id}, this)">
                <div class="notif-msg">${n.message}</div>
                <div class="notif-time">${new Date(n.created_at).toLocaleString()}</div>
            </div>
        `).join("")}
    `;
    await markAllNotificationsRead();
    loadNotificationBadge();
}

async function markAllRead() {
    await markAllNotificationsRead();
    loadNotificationBadge();
    const panel = document.getElementById("notif-panel");
    if (panel) panel.querySelectorAll(".notif-item").forEach(el => el.classList.remove("unread"));
}

async function markOneRead(id, el) {
    await markNotificationRead(id);
    el.classList.remove("unread");
    loadNotificationBadge();
}

// ATTACHMENTS
async function uploadAttachment(complaintId, file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/complaints/${complaintId}/attachments`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${getToken()}` },
        body: formData
    });
    return res.json();
}

async function getAttachments(complaintId) {
    const res = await fetch(`${API_URL}/complaints/${complaintId}/attachments`, { headers: authHeaders() });
    return res.json();
}

async function deleteAttachment(complaintId, attachmentId) {
    const res = await fetch(`${API_URL}/complaints/${complaintId}/attachments/${attachmentId}`, {
        method: "DELETE", headers: authHeaders()
    });
    return res.json();
}
