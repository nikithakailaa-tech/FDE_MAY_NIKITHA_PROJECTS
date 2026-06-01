window.onload = async function () {
    requireAuth();
    await loadComplaints();
}

async function loadComplaints() {
    try {
        const complaints = await getComplaints();
        const tbody = document.getElementById("complaints-body");
        tbody.innerHTML = "";

        if (!complaints.length) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#666;">No complaints found</td></tr>`;
            return;
        }

        complaints.forEach(c => {
            tbody.innerHTML += `
                <tr>
                    <td>${c.complaint_number}</td>
                    <td>${c.title}</td>
                    <td><span class="badge badge-${c.priority}">${c.priority}</span></td>
                    <td><span class="badge badge-${c.status}">${c.status}</span></td>
                    <td>${new Date(c.created_at).toLocaleDateString()}</td>
                    <td>${c.sla_deadline ? new Date(c.sla_deadline).toLocaleDateString() : "N/A"}</td>
                    <td>
                        <button class="btn btn-warning" onclick="openUpdate(${c.id}, '${c.status}')">Update</button>
                    </td>
                </tr>
            `;
        });
    } catch (err) {
        console.error("Failed to load complaints", err);
    }
}

async function openUpdate(id, currentStatus) {
    const newStatus = prompt(`Update status for complaint #${id}\nCurrent: ${currentStatus}\n\nEnter new status:\nopen / assigned / in_progress / pending / escalated / resolved / closed`);
    
    if (!newStatus) return;

    const note = prompt("Add a resolution note (optional):");

    try {
        const data = await updateComplaint(id, {
            status: newStatus,
            resolution_note: note || ""
        });

        if (data.id) {
            alert("Complaint updated successfully!");
            await loadComplaints();
        } else {
            alert("Update failed: " + (data.detail || "Unknown error"));
        }
    } catch (err) {
        alert("Something went wrong!");
    }
}