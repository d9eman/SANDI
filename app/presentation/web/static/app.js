(() => {
  "use strict";

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-target]");
    if (!button) return;
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target) return;
    try {
      await navigator.clipboard.writeText(target.textContent.trim());
      const original = button.textContent;
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = original; }, 1400);
    } catch (_) {
      window.prompt("Copy this value:", target.textContent.trim());
    }
  });

  function locationMessage(code) {
    if (code === 1) return "Location permission was denied. Enter a ZIP code, city, or area instead.";
    if (code === 2) return "Your browser could not determine a location. Enter a ZIP code, city, or area instead.";
    if (code === 3) return "Location lookup took too long. Enter a ZIP code, city, or area instead.";
    return "Location could not be used. Enter a ZIP code, city, or area instead.";
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-location-button]");
    if (!button) return;

    const form = document.getElementById("food-location-form");
    const locationInput = document.getElementById("food-location-input");
    const latitudeInput = document.getElementById("food-latitude");
    const longitudeInput = document.getElementById("food-longitude");
    const status = document.getElementById("location-status");
    if (!form || !locationInput || !latitudeInput || !longitudeInput || !status) {
      window.alert("The location form did not load correctly. Enter a ZIP code instead.");
      return;
    }

    if (!window.isSecureContext) {
      status.textContent = "Browser location requires HTTPS or localhost. Enter a ZIP code, city, or area instead.";
      status.classList.add("error-text");
      return;
    }
    if (!("geolocation" in navigator)) {
      status.textContent = "This browser does not support location lookup. Enter a ZIP code, city, or area instead.";
      status.classList.add("error-text");
      return;
    }

    const original = button.textContent;
    button.disabled = true;
    button.textContent = "Getting location…";
    status.classList.remove("error-text");
    status.textContent = "Waiting for browser permission…";

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        latitudeInput.value = coords.latitude.toFixed(6);
        longitudeInput.value = coords.longitude.toFixed(6);
        if (!locationInput.value.trim()) locationInput.value = "Current location";
        status.textContent = "Location found. Loading nearby options…";
        button.textContent = "Location found";
        form.requestSubmit();
      },
      (error) => {
        status.textContent = locationMessage(error.code);
        status.classList.add("error-text");
        button.textContent = original;
        button.disabled = false;
      },
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 300000 }
    );
  });
})();
