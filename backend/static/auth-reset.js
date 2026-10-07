(() => {
  "use strict";

  const root = document.querySelector("#root");
  if (!root) return;

  const RESET_TOKEN_PARAM = "reset_token";
  let resetViewActive = false;
  let observerStarted = false;

  function escapeHtml(value = "") {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getResetToken() {
    return new URL(window.location.href).searchParams.get(RESET_TOKEN_PARAM) || "";
  }

  async function postJson(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    });

    let data = {};
    try {
      data = await response.json();
    } catch (_error) {
      data = {};
    }

    if (!response.ok) {
      const message = data.message || "Something went wrong. Please try again.";
      const error = new Error(message);
      error.payload = data;
      throw error;
    }

    return data;
  }

  function clearResetTokenFromUrl() {
    const url = new URL(window.location.href);
    url.searchParams.delete(RESET_TOKEN_PARAM);
    window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
  }

  function showForgotView(email = "") {
    resetViewActive = true;
    root.innerHTML = `
      <div class="reset-shell">
        <main class="reset-card" id="main-content">
          <span class="eyebrow">Account recovery</span>
          <h1>Forgot your password?</h1>
          <p class="muted">Enter the email connected to your AI Career Navigator account. We will generate a secure password-reset link.</p>
          <form id="forgot-password-form">
            <label>Email
              <input id="forgot-email" name="email" type="email" autocomplete="email" value="${escapeHtml(email)}" required>
            </label>
            <p id="forgot-error" class="error-text" role="alert" hidden></p>
            <p id="forgot-success" class="success-text" role="status" hidden></p>
            <div id="forgot-dev-note" class="reset-dev-note" hidden></div>
            <div class="button-row">
              <button type="button" id="forgot-back" class="button secondary">Back to sign in</button>
              <button type="submit" class="button primary">Send reset link</button>
            </div>
          </form>
        </main>
      </div>`;

    const form = document.querySelector("#forgot-password-form");
    const emailInput = document.querySelector("#forgot-email");
    const errorBox = document.querySelector("#forgot-error");
    const successBox = document.querySelector("#forgot-success");
    const devNote = document.querySelector("#forgot-dev-note");

    document.querySelector("#forgot-back").addEventListener("click", () => {
      window.location.reload();
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.hidden = true;
      successBox.hidden = true;
      devNote.hidden = true;

      const submitButton = form.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.textContent = "Sending…";

      try {
        const data = await postJson("/api/forgot-password", {
          email: emailInput.value.trim(),
        });

        successBox.textContent = data.message || "If that email is registered, a reset link has been prepared.";
        successBox.hidden = false;

        if (data.debug_reset_url) {
          devNote.innerHTML = `Development mode: email delivery is not configured yet. Use this reset link for local testing:<br><a href="${escapeHtml(data.debug_reset_url)}">${escapeHtml(data.debug_reset_url)}</a>`;
          devNote.hidden = false;
        }
      } catch (error) {
        errorBox.textContent = error.message || "Unable to send the reset link.";
        errorBox.hidden = false;
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Send reset link";
      }
    });

    emailInput.focus();
  }

  function showResetView(token) {
    resetViewActive = true;
    root.innerHTML = `
      <div class="reset-shell">
        <main class="reset-card" id="main-content">
          <span class="eyebrow">Account recovery</span>
          <h1>Create a new password</h1>
          <p class="muted">Choose a new password with at least 8 characters. This reset link expires shortly and can only be used once.</p>
          <form id="reset-password-form">
            <label>New password
              <input id="reset-password" name="password" type="password" autocomplete="new-password" minlength="8" required>
            </label>
            <label>Confirm new password
              <input id="reset-password-confirm" name="password_confirm" type="password" autocomplete="new-password" minlength="8" required>
            </label>
            <p id="reset-error" class="error-text" role="alert" hidden></p>
            <p id="reset-success" class="success-text" role="status" hidden></p>
            <div class="button-row">
              <button type="button" id="reset-cancel" class="button secondary">Back to sign in</button>
              <button type="submit" class="button primary">Update password</button>
            </div>
          </form>
        </main>
      </div>`;

    const form = document.querySelector("#reset-password-form");
    const passwordInput = document.querySelector("#reset-password");
    const confirmInput = document.querySelector("#reset-password-confirm");
    const errorBox = document.querySelector("#reset-error");
    const successBox = document.querySelector("#reset-success");

    document.querySelector("#reset-cancel").addEventListener("click", () => {
      clearResetTokenFromUrl();
      window.location.reload();
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.hidden = true;
      successBox.hidden = true;

      if (passwordInput.value !== confirmInput.value) {
        errorBox.textContent = "The two passwords do not match.";
        errorBox.hidden = false;
        return;
      }

      if (passwordInput.value.length < 8) {
        errorBox.textContent = "Password must be at least 8 characters.";
        errorBox.hidden = false;
        return;
      }

      const submitButton = form.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.textContent = "Updating…";

      try {
        const data = await postJson("/api/reset-password", {
          token,
          password: passwordInput.value,
        });

        successBox.textContent = data.message || "Password updated successfully. You can now sign in.";
        successBox.hidden = false;
        form.querySelectorAll("input, button").forEach((element) => {
          element.disabled = true;
        });

        setTimeout(() => {
          clearResetTokenFromUrl();
          window.location.reload();
        }, 1200);
      } catch (error) {
        errorBox.textContent = error.message || "Unable to reset the password.";
        errorBox.hidden = false;
        submitButton.disabled = false;
        submitButton.textContent = "Update password";
      }
    });

    passwordInput.focus();
  }

  function injectForgotLink() {
    if (resetViewActive) return;
    const form = document.querySelector("#auth-form");
    if (!form) return;

    // Registration form contains a name field; forgot password belongs only on sign-in.
    if (form.querySelector('input[name="name"]')) return;
    if (form.querySelector(".auth-forgot-wrap")) return;

    const wrapper = document.createElement("div");
    wrapper.className = "auth-forgot-wrap";
    wrapper.innerHTML = '<button type="button" class="auth-forgot">Forgot password?</button>';
    wrapper.querySelector(".auth-forgot").addEventListener("click", () => {
      const email = form.querySelector('input[name="email"]')?.value?.trim() || "";
      showForgotView(email);
    });

    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.parentNode.insertBefore(wrapper, submitButton);
    } else {
      form.appendChild(wrapper);
    }
  }

  function startObserver() {
    if (observerStarted) return;
    observerStarted = true;

    const observer = new MutationObserver(() => {
      if (!resetViewActive) injectForgotLink();
    });
    observer.observe(root, { childList: true, subtree: true });

    setTimeout(injectForgotLink, 0);
    setTimeout(injectForgotLink, 150);
    setTimeout(injectForgotLink, 500);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const token = getResetToken();
    if (token) {
      showResetView(token);
      return;
    }
    startObserver();
  });
})();
