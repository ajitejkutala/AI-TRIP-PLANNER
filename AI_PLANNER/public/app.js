// Smart Travel Planner Frontend Logic

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const form = document.getElementById("planner-form");
  const cityInput = document.getElementById("city-input");
  const interestsInput = document.getElementById("interests-input");
  const durationSelect = document.getElementById("duration-select");
  const paceSelect = document.getElementById("pace-select");
  const customKeyInput = document.getElementById("custom-key-input");
  const generateBtn = document.getElementById("generate-btn");
  
  const loadingCard = document.getElementById("loading-card");
  const loadingQuote = document.getElementById("loading-quote");
  const errorCard = document.getElementById("error-card");
  const errorTitle = document.getElementById("error-title");
  const errorMessage = document.getElementById("error-message");
  const dismissErrorBtn = document.getElementById("dismiss-error-btn");
  
  const resultCard = document.getElementById("result-card");
  const resultDestinationBadge = document.getElementById("result-destination-badge");
  const resultDurationBadge = document.getElementById("result-duration-badge");
  const resultCuratedBadge = document.getElementById("result-curated-badge");
  const itineraryContent = document.getElementById("itinerary-content");
  
  const downloadPdfBtn = document.getElementById("download-pdf-btn");
  const copyBtn = document.getElementById("copy-btn");
  const printBtn = document.getElementById("print-btn");
  const resetBtn = document.getElementById("reset-btn");
  const toast = document.getElementById("toast");

  const toggleSettingsBtn = document.getElementById("toggle-settings-btn");
  const settingsContent = document.getElementById("settings-content");
  const settingsChevron = document.getElementById("settings-chevron");

  const pdfBranding = document.getElementById("pdf-branding");
  const pdfDate = document.getElementById("pdf-date");
  const pdfCity = document.getElementById("pdf-city");
  const pdfDuration = document.getElementById("pdf-duration");
  const pdfInterests = document.getElementById("pdf-interests");

  // State
  let currentRawItinerary = "";
  let currentCity = "";
  let currentDuration = "";
  let currentInterests = "";
  let quoteInterval = null;
  let stepInterval = null;

  const travelQuotes = [
    '"Traveling – it leaves you speechless, then turns you into a storyteller." – Ibn Battuta',
    '"To travel is to live." – Hans Christian Andersen',
    '"The journey of a thousand miles begins with a single step." – Lao Tzu',
    '"Life is either a daring adventure or nothing at all." – Helen Keller',
    '"Travel brings power and love back to your life." – Rumi',
    '"A good traveler has no fixed plans, and is not intent on arriving." – Lao Tzu'
  ];

  // Backend Health Ping with auto-fallback route
  async function pingHealth() {
    try {
      let r = await fetch("/api/health");
      if (r.status === 404) {
        r = await fetch("/health");
      }
      const data = await r.json();
      console.log("Backend status:", data);
    } catch (err) {
      console.warn("Backend health ping:", err);
    }
  }
  pingHealth();

  // Toggle Advanced Settings Accordion
  toggleSettingsBtn.addEventListener("click", () => {
    const isOpen = settingsContent.classList.toggle("open");
    settingsChevron.textContent = isOpen ? "▴" : "▾";
  });

  // Quick City Chips
  document.querySelectorAll(".chip-city").forEach(chip => {
    chip.addEventListener("click", () => {
      const city = chip.getAttribute("data-city");
      cityInput.value = city;
      cityInput.focus();
    });
  });

  // Quick Interest Chips
  document.querySelectorAll(".chip-interest").forEach(chip => {
    chip.addEventListener("click", () => {
      const interest = chip.getAttribute("data-interest");
      let currentVal = interestsInput.value.trim();
      let parts = currentVal ? currentVal.split(",").map(p => p.trim()) : [];

      const index = parts.findIndex(p => p.toLowerCase() === interest.toLowerCase());
      if (index === -1) {
        parts.push(interest);
        chip.classList.add("active");
      } else {
        parts.splice(index, 1);
        chip.classList.remove("active");
      }

      interestsInput.value = parts.join(", ");
    });
  });

  // Synchronize interest chip active state when typing manually
  interestsInput.addEventListener("input", () => {
    const text = interestsInput.value.toLowerCase();
    document.querySelectorAll(".chip-interest").forEach(chip => {
      const interest = chip.getAttribute("data-interest").toLowerCase();
      if (text.includes(interest)) {
        chip.classList.add("active");
      } else {
        chip.classList.remove("active");
      }
    });
  });

  // Dismiss Error
  dismissErrorBtn.addEventListener("click", () => {
    errorCard.style.display = "none";
  });

  // Live Sequencer for Generation Loading State
  function startJourneyAnimation() {
    const stepItems = document.querySelectorAll(".step-item");
    let currentStep = 0;

    stepItems.forEach(item => {
      item.classList.remove("active", "completed");
    });
    if (stepItems[0]) stepItems[0].classList.add("active");

    stepInterval = setInterval(() => {
      if (currentStep < stepItems.length - 1) {
        stepItems[currentStep].classList.remove("active");
        stepItems[currentStep].classList.add("completed");
        currentStep++;
        stepItems[currentStep].classList.add("active");
      }
    }, 1100);

    let quoteIndex = 0;
    loadingQuote.textContent = travelQuotes[quoteIndex];
    quoteInterval = setInterval(() => {
      quoteIndex = (quoteIndex + 1) % travelQuotes.length;
      loadingQuote.textContent = travelQuotes[quoteIndex];
    }, 2800);
  }

  function stopJourneyAnimation() {
    if (stepInterval) clearInterval(stepInterval);
    if (quoteInterval) clearInterval(quoteInterval);
    stepInterval = null;
    quoteInterval = null;
  }

  // Form Submit Handler
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const city = cityInput.value.trim();
    const interests = interestsInput.value.trim();
    const duration = durationSelect.value;
    const pace = paceSelect.value;
    const customKey = customKeyInput.value.trim();

    if (!city) {
      showError("Please enter a destination city.");
      cityInput.focus();
      return;
    }

    if (!interests) {
      showError("Please enter at least one interest or choose tags above.");
      interestsInput.focus();
      return;
    }

    currentCity = city;
    currentDuration = duration;
    currentInterests = interests;

    // Reset UI states
    errorCard.style.display = "none";
    resultCard.style.display = "none";
    loadingCard.style.display = "block";
    generateBtn.disabled = true;

    startJourneyAnimation();
    loadingCard.scrollIntoView({ behavior: "smooth", block: "nearest" });

    try {
      const payload = {
        city: city,
        interests: interests,
        duration: duration,
        pace: pace,
        api_key: customKey || null
      };

      // Resilient fetch with fallback path for Vercel/proxies
      let response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (response.status === 404) {
        response = await fetch("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (err) {
        throw new Error(`Server returned unexpected response (status ${response.status}): ${text.slice(0, 160)}`);
      }

      if (!response.ok) {
        throw new Error(data.detail || data.error || `Failed to generate itinerary (Status ${response.status}).`);
      }

      displayItinerary(data);

    } catch (err) {
      console.error("Trip planning error:", err);
      showError(err.message || "An unexpected error occurred while generating your plan.");
    } finally {
      stopJourneyAnimation();
      loadingCard.style.display = "none";
      generateBtn.disabled = false;
    }
  });

  // Display itinerary with staggered animations
  function displayItinerary(data) {
    currentRawItinerary = data.itinerary;

    // Badges
    resultDestinationBadge.textContent = `📍 ${data.city}`;
    resultDurationBadge.textContent = `⏱️ ${data.duration} (${data.pace})`;
    if (resultCuratedBadge && data.model) {
      resultCuratedBadge.textContent = `✨ ${data.model}`;
    }

    // Render Markdown
    let rawHtml = "";
    if (typeof marked !== "undefined" && marked.parse) {
      rawHtml = marked.parse(data.itinerary);
    } else {
      rawHtml = escapeHtml(data.itinerary).replace(/\n/g, "<br>");
    }

    // Wrap top-level sections into staggered animation blocks
    itineraryContent.innerHTML = enhanceWithStaggeredAnimations(rawHtml);

    resultCard.style.display = "block";
    resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Splits HTML on h2/h1 tags to inject staggered animation classes
  function enhanceWithStaggeredAnimations(html) {
    const parts = html.split(/(?=<h[123])/g);
    return parts.map((part, index) => {
      const delay = (index * 0.08).toFixed(2);
      return `<div class="itinerary-section" style="animation-delay: ${delay}s">${part}</div>`;
    }).join("");
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorCard.style.display = "flex";
    errorCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // High-Reliability Vector PDF Download Feature with resilient endpoint fallback
  downloadPdfBtn.addEventListener("click", async () => {
    if (!currentRawItinerary) return;

    const originalBtnText = downloadPdfBtn.innerHTML;
    downloadPdfBtn.innerHTML = `<span class="tool-icon">⏳</span> Generating PDF...`;
    downloadPdfBtn.disabled = true;

    const safeCity = (currentCity || "Trip").replace(/[^a-zA-Z0-9]/g, "_");
    const safeFilename = `${safeCity}_Day_Trip_Itinerary.pdf`;

    try {
      const pdfPayload = {
        city: currentCity || "Destination",
        duration: currentDuration || "1 Day",
        interests: currentInterests || "Sightseeing",
        itinerary: currentRawItinerary
      };

      // 1. Request true vector PDF from server endpoint with fallback route
      let response = await fetch("/api/download-pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(pdfPayload)
      });

      if (response.status === 404) {
        response = await fetch("/download-pdf", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(pdfPayload)
        });
      }

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      // 2. Stream blob and trigger immediate browser download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const downloadLink = document.createElement("a");
      downloadLink.style.display = "none";
      downloadLink.href = downloadUrl;
      downloadLink.download = safeFilename;

      document.body.appendChild(downloadLink);
      downloadLink.click();

      setTimeout(() => {
        window.URL.revokeObjectURL(downloadUrl);
        if (document.body.contains(downloadLink)) {
          document.body.removeChild(downloadLink);
        }
      }, 1500);

      showToast("📄 Complete PDF Downloaded Successfully! 🎉");

    } catch (err) {
      console.warn("Direct PDF endpoint issue, opening print dialog as fallback:", err);
      // Fallback: trigger standard browser print dialog
      window.print();
    } finally {
      downloadPdfBtn.innerHTML = originalBtnText;
      downloadPdfBtn.disabled = false;
    }
  });

  // Copy to clipboard
  copyBtn.addEventListener("click", () => {
    if (!currentRawItinerary) return;
    navigator.clipboard.writeText(currentRawItinerary).then(() => {
      showToast("📋 Itinerary copied to clipboard!");
    }).catch(err => {
      console.error("Copy failed:", err);
      showToast("Could not copy text.");
    });
  });

  // Print
  printBtn.addEventListener("click", () => {
    window.print();
  });

  // Reset / Plan new trip
  resetBtn.addEventListener("click", () => {
    cityInput.value = "";
    interestsInput.value = "";
    document.querySelectorAll(".chip-interest").forEach(c => c.classList.remove("active"));
    resultCard.style.display = "none";
    cityInput.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // Toast Notification
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2800);
  }
});
