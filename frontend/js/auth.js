// HANDLE LOGIN
async function handleLogin() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const alertBox = document.getElementById("alert-box");

    if (!email || !password) {
        alertBox.innerHTML = `<div class="alert alert-error">Please fill in all fields!</div>`;
        return;
    }

    try {
        const data = await loginUser(email, password);

        if (data.access_token) {
            saveToken(data.access_token);
            window.location.href = "/app/dashboard";
        } else {
            alertBox.innerHTML = `<div class="alert alert-error">${data.detail || "Login failed!"}</div>`;
        }
    } catch (err) {
        alertBox.innerHTML = `<div class="alert alert-error">Something went wrong. Try again!</div>`;
    }
}

// HANDLE REGISTER
async function handleRegister() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const alertBox = document.getElementById("alert-box");

    if (!name || !email || !password) {
        alertBox.innerHTML = `<div class="alert alert-error">Please fill in all fields!</div>`;
        return;
    }

    try {
        const data = await registerUser(name, email, password, role);

        if (data.id) {
            alertBox.innerHTML = `<div class="alert alert-success">Registration successful! Please login.</div>`;
            setTimeout(() => {
                window.location.href = "/";
            }, 1500);
        } else {
            alertBox.innerHTML = `<div class="alert alert-error">${data.detail || "Registration failed!"}</div>`;
        }
    } catch (err) {
        alertBox.innerHTML = `<div class="alert alert-error">Something went wrong. Try again!</div>`;
    }
}