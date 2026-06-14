(() => {
  const root = document.documentElement;

  // YEAR
  const y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();

  // THEME
  const themeBtn = document.getElementById("themeToggle");
  function setTheme(t) {
    root.setAttribute("data-theme", t);
    localStorage.setItem("theme", t);
  }

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const current = root.getAttribute("data-theme") || "light";
      setTheme(current === "dark" ? "light" : "dark");
    });
  }

  const themeSelect = document.getElementById("themeSelect");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
  const applyThemePreference = (value) => {
    if (value === "system") {
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
      localStorage.setItem("themePreference", "system");
      return;
    }
    setTheme(value);
    localStorage.setItem("themePreference", value);
  };

  if (themeSelect) {
    themeSelect.addEventListener("change", async () => {
      const theme = themeSelect.value;
      applyThemePreference(theme);

      await fetch("/api/theme", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken || "",
        },
        body: JSON.stringify({ theme }),
      });
    });
  }

  // DROPDOWNS
  const dotsBtn = document.getElementById("dotsBtn");
  const dotsMenu = document.getElementById("dotsMenu");
  const avatarBtn = document.getElementById("avatarBtn");
  const avatarMenu = document.getElementById("avatarMenu");

  function closeDropdowns() {
    if (dotsMenu) dotsMenu.classList.remove("open");
    if (avatarMenu) avatarMenu.classList.remove("open");
  }

  if (dotsBtn && dotsMenu) {
    dotsBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = dotsMenu.classList.toggle("open");
      if (open && avatarMenu) avatarMenu.classList.remove("open");
    });
  }

  if (avatarBtn && avatarMenu) {
    avatarBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = avatarMenu.classList.toggle("open");
      if (open && dotsMenu) dotsMenu.classList.remove("open");
    });
  }

  document.addEventListener("click", closeDropdowns);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDropdowns();
  });

  // MOBILE MENU (pages + close)
  const hamburger = document.getElementById("hamburger");
  const mobileMenu = document.getElementById("mobileMenu");
  const closeMenu = document.getElementById("closeMenu");

  function openMobile() {
    if (!mobileMenu) return;
    mobileMenu.classList.add("isOpen");
    mobileMenu.setAttribute("aria-hidden", "false");
    if (hamburger) hamburger.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function closeMobile() {
    if (!mobileMenu) return;
    mobileMenu.classList.remove("isOpen");
    mobileMenu.setAttribute("aria-hidden", "true");
    if (hamburger) hamburger.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  if (hamburger) hamburger.addEventListener("click", openMobile);
  if (closeMenu) closeMenu.addEventListener("click", closeMobile);

  if (mobileMenu) {
    mobileMenu.addEventListener("click", (e) => {
      if (e.target === mobileMenu) closeMobile(); // click outside panel
    });

    mobileMenu.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", closeMobile);
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMobile();
  });

  // BACK TO TOP
  const toTop = document.getElementById("toTop");
  if (toTop) {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 450) toTop.classList.add("show");
      else toTop.classList.remove("show");
    });
    toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  // SECRET OFFER
  const secretOfferForm = document.getElementById("secretOfferForm");
  const secretOfferCode = document.getElementById("secretOfferCode");
  const secretOfferResult = document.getElementById("secretOfferResult");
  if (secretOfferForm && secretOfferCode && secretOfferResult) {
    secretOfferForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      secretOfferResult.hidden = false;
      secretOfferResult.className = "secretOfferResult";
      secretOfferResult.textContent = "Checking code...";

      const response = await fetch("/api/secret-offer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken || "",
        },
        body: JSON.stringify({ code: secretOfferCode.value }),
      });

      const payload = await response.json();
      if (!payload.ok) {
        secretOfferResult.classList.add("secretOfferResult--error");
        secretOfferResult.textContent = payload.error || "Invalid secret code.";
        return;
      }

      const items = payload.offer.includes.map((item) => `<li>${item}</li>`).join("");
      secretOfferResult.classList.add("secretOfferResult--success");
      secretOfferResult.innerHTML = `
        <div class="secretOfferPrice">${payload.offer.price}</div>
        <strong>${payload.offer.name}</strong>
        <ul>${items}</ul>
      `;
    });
  }

  // FIRST-TIME DASHBOARD TOUR
  const tour = document.getElementById("onboardingTour");
  const tourTitle = document.getElementById("onboardingTitle");
  const tourBody = document.getElementById("onboardingBody");
  const tourCount = document.getElementById("onboardingCount");
  const tourBar = document.getElementById("onboardingBar");
  const tourBack = document.getElementById("onboardingBack");
  const tourNext = document.getElementById("onboardingNext");
  const tourSteps = [
    {
      target: "overview",
      title: "Welcome to your dashboard",
      body: "This is your home base after signup. You can return here to manage your account, find quick links, and unlock private website features.",
    },
    {
      target: "stats",
      title: "Quick profile summary",
      body: "These cards show a fast snapshot of the portfolio: projects, core skills, and active status.",
    },
    {
      target: "links",
      title: "Move around faster",
      body: "Quick links help you jump to public pages, settings, profile, and admin tools when your account has access.",
    },
    {
      target: "offer",
      title: "Private offer area",
      body: "Use the secret code feature to reveal a special package price. This is a demo of protected user-only functionality.",
    },
    {
      target: "actions",
      title: "Account actions",
      body: "Use these buttons to update your profile, open admin tools, or return to the project showcase.",
    },
  ];
  let tourIndex = 0;

  function clearTourFocus() {
    document.querySelectorAll(".tourFocus").forEach((node) => node.classList.remove("tourFocus"));
  }

  async function completeTour() {
    clearTourFocus();
    if (tour) {
      tour.classList.remove("isOpen");
      tour.setAttribute("aria-hidden", "true");
    }
    document.body.style.overflow = "";

    await fetch("/api/onboarding/complete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken || "",
      },
      body: "{}",
    }).catch(() => {});
  }

  function renderTourStep() {
    if (!tour || !tourTitle || !tourBody || !tourCount || !tourBar || !tourBack || !tourNext) return;
    const step = tourSteps[tourIndex];
    clearTourFocus();

    const target = document.querySelector(`[data-tour-target="${step.target}"]`);
    if (target) {
      target.classList.add("tourFocus");
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    tourTitle.textContent = step.title;
    tourBody.textContent = step.body;
    tourCount.textContent = `${tourIndex + 1} of ${tourSteps.length}`;
    tourBar.style.width = `${((tourIndex + 1) / tourSteps.length) * 100}%`;
    tourBack.disabled = tourIndex === 0;
    tourNext.textContent = tourIndex === tourSteps.length - 1 ? "Finish" : "Next";
  }

  if (tour) {
    window.setTimeout(() => {
      tour.classList.add("isOpen");
      tour.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      renderTourStep();
    }, 450);

    if (tourBack) {
      tourBack.addEventListener("click", () => {
        tourIndex = Math.max(0, tourIndex - 1);
        renderTourStep();
      });
    }
    if (tourNext) {
      tourNext.addEventListener("click", () => {
        if (tourIndex >= tourSteps.length - 1) {
          completeTour();
          return;
        }
        tourIndex += 1;
        renderTourStep();
      });
    }
    tour.querySelectorAll("[data-tour-close]").forEach((button) => {
      button.addEventListener("click", completeTour);
    });
  }

  // PROJECT QUOTE BUILDER
  const quoteForm = document.getElementById("quoteForm");
  const quotePrice = document.getElementById("quotePrice");
  const quoteTime = document.getElementById("quoteTime");
  const quoteStack = document.getElementById("quoteStack");
  const quoteIncludes = document.getElementById("quoteIncludes");
  const quoteComplexity = document.getElementById("quoteComplexity");
  const quoteEmail = document.getElementById("quoteEmail");
  const quoteReset = document.getElementById("quoteReset");
  const quoteBudget = document.getElementById("quoteBudget");
  const proposalDownload = document.getElementById("proposalDownload");
  const mlPredict = document.getElementById("mlPredict");
  const saveQuote = document.getElementById("saveQuote");
  const saveQuoteStatus = document.getElementById("saveQuoteStatus");
  const mlSuccessScore = document.getElementById("mlSuccessScore");
  const mlPackage = document.getElementById("mlPackage");
  const mlRisk = document.getElementById("mlRisk");
  const mlModel = document.getElementById("mlModel");
  const mlAdvice = document.getElementById("mlAdvice");
  const roadmapTotal = document.getElementById("roadmapTotal");
  const roadmapTimeline = document.getElementById("roadmapTimeline");
  const roadmapChecklist = document.getElementById("roadmapChecklist");
  let latestMlPrediction = null;
  let latestPredictionId = null;
  let mlTimer = null;

  const quoteTypes = {
    portfolio: {
      label: "Portfolio website",
      min: 35,
      max: 60,
      daysMin: 2,
      daysMax: 4,
      stack: "HTML, CSS, JavaScript, Flask",
      includes: ["Responsive portfolio layout", "Projects section", "Contact buttons"],
    },
    business: {
      label: "Business website",
      min: 60,
      max: 100,
      daysMin: 3,
      daysMax: 5,
      stack: "HTML, CSS, JavaScript, Flask",
      includes: ["Services pages", "Contact section", "Trust-focused layout"],
    },
    store: {
      label: "Store website",
      min: 90,
      max: 160,
      daysMin: 5,
      daysMax: 8,
      stack: "Flask, SQLite, HTML, CSS, JavaScript",
      includes: ["Product cards", "Order flow", "Basic store structure"],
    },
    dashboard: {
      label: "Dashboard app",
      min: 110,
      max: 220,
      daysMin: 6,
      daysMax: 10,
      stack: "Python, Flask, SQLite, HTML, CSS, JavaScript",
      includes: ["Protected dashboard", "User flow", "Data screens"],
    },
  };

  const quoteFeatures = {
    contact: { label: "Contact form and social buttons", min: 10, max: 20, days: 1 },
    auth: { label: "Login and signup system", min: 25, max: 45, days: 2 },
    socialAuth: { label: "Google or Facebook login", min: 30, max: 60, days: 2 },
    admin: { label: "Admin dashboard", min: 45, max: 90, days: 3 },
    database: { label: "Database setup", min: 25, max: 55, days: 2 },
    payments: { label: "Payment page setup", min: 45, max: 100, days: 3 },
  };

  function selectedQuoteFeatures() {
    return Array.from(quoteForm.querySelectorAll('input[name="features"]:checked')).map((input) => input.value);
  }

  function formatRange(min, max, prefix = "", suffix = "") {
    return `${prefix}${min}${suffix} - ${prefix}${max}${suffix}`;
  }

  function expandedFeatureSet(payload) {
    const features = new Set(payload.features || []);
    if (features.has("socialAuth")) features.add("auth");
    if (["store", "dashboard"].includes(payload.projectType)) features.add("database");
    return features;
  }

  function buildRoadmap(payload, prediction) {
    const type = quoteTypes[payload.projectType] || quoteTypes.portfolio;
    const features = expandedFeatureSet(payload);
    const predictedMax = Number(prediction?.days_max || 0);
    const typeMax = type.daysMax + Math.max(Math.ceil((payload.pages - 3) / 2), 0);
    const targetDays = Math.max(predictedMax || typeMax, 5);

    const phases = [
      {
        title: "Discovery",
        detail: `Confirm ${type.label} goals, pages, content, and success target.`,
        weight: 1,
      },
      {
        title: "UI Design",
        detail: "Design the main screens, responsive layout, buttons, and visual style.",
        weight: payload.pages >= 5 ? 2 : 1,
      },
      {
        title: "Frontend Build",
        detail: "Build polished pages, forms, interactions, and mobile behavior.",
        weight: Math.max(1, Math.ceil(payload.pages / 3)),
      },
    ];

    if (features.has("auth")) {
      phases.push({
        title: "Account System",
        detail: "Add signup, login, logout, sessions, validation, and protected pages.",
        weight: 2,
      });
    }

    if (features.has("socialAuth")) {
      phases.push({
        title: "OAuth Setup",
        detail: "Connect Google/Facebook login, callback URLs, and real provider settings.",
        weight: 2,
      });
    }

    if (features.has("database")) {
      phases.push({
        title: "Data Layer",
        detail: "Create database tables, save important actions, and prepare admin data.",
        weight: 2,
      });
    }

    if (features.has("admin")) {
      phases.push({
        title: "Admin Panel",
        detail: "Add owner-only stats, recent activity, controls, and clean dashboards.",
        weight: 2,
      });
    }

    if (features.has("payments")) {
      phases.push({
        title: "Payment Flow",
        detail: "Prepare checkout screens, order states, and payment safety checks.",
        weight: 2,
      });
    }

    phases.push(
      {
        title: "Testing",
        detail: "Test forms, login, mobile screens, broken links, and main user paths.",
        weight: payload.deadline === "urgent" ? 1 : 2,
      },
      {
        title: "Launch",
        detail: "Deploy, check live URLs, prepare handoff notes, and confirm analytics.",
        weight: 1,
      }
    );

    const totalWeight = phases.reduce((sum, phase) => sum + phase.weight, 0);
    let usedDays = 0;

    return phases.map((phase, index) => {
      const remainingPhases = phases.length - index;
      const remainingDays = Math.max(remainingPhases, targetDays - usedDays);
      const maxForThisPhase = Math.max(1, remainingDays - (remainingPhases - 1));
      const suggestedDays = Math.max(1, Math.round((phase.weight / totalWeight) * targetDays));
      const duration = index === phases.length - 1 ? remainingDays : Math.min(maxForThisPhase, suggestedDays);
      const start = usedDays + 1;
      usedDays += duration;
      const end = usedDays;

      return {
        ...phase,
        range: start === end ? `Day ${start}` : `Days ${start}-${end}`,
      };
    });
  }

  function buildLaunchChecklist(payload) {
    const features = expandedFeatureSet(payload);
    const items = [
      "Final text, images, links, and brand name are ready.",
      "Test the full website on phone, tablet, and desktop.",
      "Check every contact, GitHub, YouTube, and email link.",
    ];

    if (features.has("auth")) {
      items.push("Create a real test account and check logout/session behavior.");
    }
    if (features.has("socialAuth")) {
      items.push("Add the final public OAuth redirect URLs before deployment.");
    }
    if (features.has("database") || features.has("admin")) {
      items.push("Create the owner admin account and test saved data.");
    }
    if (features.has("payments")) {
      items.push("Use sandbox payments first, then enable live keys only after testing.");
    }
    if (payload.deadline === "urgent") {
      items.push("Freeze new features before launch so testing stays clean.");
    }

    return items.slice(0, 7);
  }

  function renderRoadmap(payload) {
    if (!roadmapTimeline || !roadmapChecklist) return [];

    const roadmap = buildRoadmap(payload, latestMlPrediction);

    if (roadmapTotal) {
      roadmapTotal.textContent = latestMlPrediction
        ? `${latestMlPrediction.days_min}-${latestMlPrediction.days_max} day ML plan`
        : "Auto plan";
    }

    roadmapTimeline.innerHTML = roadmap.map((phase, index) => `
      <div class="roadmapStep">
        <div class="roadmapStep__marker">${index + 1}</div>
        <div class="roadmapStep__body">
          <span>${phase.range}</span>
          <strong>${phase.title}</strong>
          <p>${phase.detail}</p>
        </div>
      </div>
    `).join("");

    roadmapChecklist.innerHTML = buildLaunchChecklist(payload).map((item) => `<li>${item}</li>`).join("");
    return roadmap;
  }

  function updateQuote() {
    if (!quoteForm || !quotePrice || !quoteTime || !quoteStack || !quoteIncludes || !quoteEmail) return;

    const typeValue = quoteForm.querySelector('input[name="projectType"]:checked')?.value || "portfolio";
    const type = quoteTypes[typeValue];
    const pages = Number(document.getElementById("quotePages")?.value || 3);
    const deadline = document.getElementById("quoteDeadline")?.value || "normal";
    const budget = quoteBudget?.value || "medium";
    const features = selectedQuoteFeatures();
    const effectiveFeatures = new Set(features);

    if (features.includes("socialAuth")) {
      effectiveFeatures.add("auth");
    }
    if (["store", "dashboard"].includes(typeValue)) {
      effectiveFeatures.add("database");
    }

    let min = type.min + Math.max(pages - 1, 0) * 8;
    let max = type.max + Math.max(pages - 1, 0) * 14;
    let daysMin = type.daysMin + Math.max(Math.ceil((pages - 3) / 2), 0);
    let daysMax = type.daysMax + Math.max(Math.ceil((pages - 3) / 2), 0);
    const includes = [...type.includes];

    effectiveFeatures.forEach((featureKey) => {
      const feature = quoteFeatures[featureKey];
      if (!feature) return;
      min += feature.min;
      max += feature.max;
      daysMax += feature.days;
      includes.push(feature.label);
    });

    if (deadline === "fast") {
      min = Math.round(min * 1.18);
      max = Math.round(max * 1.25);
      daysMin = Math.max(1, daysMin - 1);
      daysMax = Math.max(daysMin + 1, daysMax - 2);
    }

    if (deadline === "urgent") {
      min = Math.round(min * 1.35);
      max = Math.round(max * 1.5);
      daysMin = Math.max(1, daysMin - 2);
      daysMax = Math.max(daysMin + 1, daysMax - 3);
    }

    const complexity = max >= 250 ? "Advanced" : max >= 130 ? "Medium" : "Starter";
    const uniqueIncludes = [...new Set(includes)].slice(0, 8);

    quotePrice.textContent = formatRange(min, max, "$");
    quoteTime.textContent = formatRange(daysMin, daysMax, "", " days");
    quoteStack.textContent = type.stack;
    if (quoteComplexity) quoteComplexity.textContent = complexity;
    quoteIncludes.innerHTML = uniqueIncludes.map((item) => `<li>${item}</li>`).join("");
    const roadmap = renderRoadmap({ projectType: typeValue, pages, deadline, budget, features });

    const body = [
      "Hi Ahmed,",
      "",
      "I used your Project Quote Builder and I want to discuss this project:",
      "",
      `Project type: ${type.label}`,
      `Pages: ${pages}`,
      `Budget: ${budget}`,
      `Features: ${uniqueIncludes.join(", ")}`,
      `Estimated price: ${quotePrice.textContent}`,
      `Estimated time: ${quoteTime.textContent}`,
      `Recommended stack: ${type.stack}`,
      latestMlPrediction ? `ML package: ${latestMlPrediction.package}` : "",
      latestMlPrediction ? `ML success score: ${latestMlPrediction.success_score}/100` : "",
      latestMlPrediction ? `ML risk: ${latestMlPrediction.risk}` : "",
      roadmap.length ? `Roadmap: ${roadmap.map((phase) => `${phase.range} ${phase.title}`).join(" | ")}` : "",
      "",
      "Can we talk about the details?",
    ].filter(Boolean).join("\n");

    const params = new URLSearchParams({
      view: "cm",
      fs: "1",
      to: quoteForm.dataset.contactEmail || "",
      su: "Project quote request",
      body,
    });
    quoteEmail.href = `https://mail.google.com/mail/?${params.toString()}`;

    if (proposalDownload) {
      const proposalParams = new URLSearchParams({
        projectType: typeValue,
        pages: String(pages),
        deadline,
        budget,
      });
      features.forEach((feature) => proposalParams.append("features", feature));
      proposalDownload.href = `/quote/proposal.pdf?${proposalParams.toString()}`;
    }
  }

  function quotePayload() {
    return {
      projectType: quoteForm.querySelector('input[name="projectType"]:checked')?.value || "portfolio",
      pages: Number(document.getElementById("quotePages")?.value || 3),
      deadline: document.getElementById("quoteDeadline")?.value || "normal",
      budget: quoteBudget?.value || "medium",
      features: selectedQuoteFeatures(),
    };
  }

  function setMlLoading() {
    if (!mlSuccessScore || !mlPackage || !mlRisk || !mlModel || !mlAdvice) return;
    mlSuccessScore.textContent = "...";
    mlPackage.textContent = "Calculating";
    mlRisk.textContent = "--";
    mlModel.textContent = "Running local ML model...";
    mlAdvice.innerHTML = "<li>Reading project details and predicting the result.</li>";
  }

  async function runMlPrediction() {
    if (!quoteForm || !mlSuccessScore || !mlPackage || !mlRisk || !mlModel || !mlAdvice) return;
    setMlLoading();

    try {
      const response = await fetch("/api/project-prediction", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken || "",
        },
        body: JSON.stringify(quotePayload()),
      });
      const payload = await response.json();
      if (!payload.ok) throw new Error("Prediction failed");

      latestMlPrediction = payload.prediction;
      latestPredictionId = payload.prediction_id;
      mlSuccessScore.textContent = latestMlPrediction.success_score;
      mlPackage.textContent = latestMlPrediction.package;
      mlRisk.textContent = latestMlPrediction.risk;
      mlModel.textContent = latestMlPrediction.model_engine;
      mlAdvice.innerHTML = latestMlPrediction.advice.map((item) => `<li>${item}</li>`).join("");
      if (saveQuoteStatus) saveQuoteStatus.textContent = "";
      updateQuote();
    } catch (_error) {
      latestMlPrediction = null;
      latestPredictionId = null;
      mlSuccessScore.textContent = "--";
      mlPackage.textContent = "Unavailable";
      mlRisk.textContent = "--";
      mlModel.textContent = "Could not run ML prediction.";
      mlAdvice.innerHTML = "<li>Try again after restarting the Flask server.</li>";
      updateQuote();
    }
  }

  async function saveCurrentQuote() {
    if (!saveQuote || !saveQuoteStatus) return;
    if (saveQuote.dataset.authenticated !== "true") {
      saveQuoteStatus.textContent = "Login first to save this quote.";
      window.location.href = saveQuote.dataset.loginUrl || "/login";
      return;
    }
    if (!latestPredictionId) {
      saveQuoteStatus.textContent = "Run the ML prediction first.";
      return;
    }

    saveQuote.disabled = true;
    saveQuoteStatus.textContent = "Saving quote...";
    try {
      const response = await fetch("/api/quotes/save", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken || "",
        },
        body: JSON.stringify({ prediction_id: latestPredictionId }),
      });
      const payload = await response.json();
      if (!payload.ok) throw new Error(payload.error || "Could not save quote.");
      saveQuoteStatus.textContent = payload.message || "Quote saved.";
    } catch (error) {
      saveQuoteStatus.textContent = error.message || "Could not save quote.";
    } finally {
      saveQuote.disabled = false;
    }
  }

  function scheduleMlPrediction() {
    if (!quoteForm) return;
    window.clearTimeout(mlTimer);
    mlTimer = window.setTimeout(runMlPrediction, 350);
  }

  if (quoteForm) {
    quoteForm.addEventListener("input", () => {
      updateQuote();
      scheduleMlPrediction();
    });
    if (quoteReset) {
      quoteReset.addEventListener("click", () => {
        quoteForm.reset();
        updateQuote();
        scheduleMlPrediction();
      });
    }
    if (mlPredict) mlPredict.addEventListener("click", runMlPrediction);
    if (saveQuote) saveQuote.addEventListener("click", saveCurrentQuote);
    updateQuote();
    runMlPrediction();
  }
})();
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toggle-pass").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();

      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;

      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";

      // optional: change icon style
      btn.classList.toggle("active", isHidden);
    });
  });
});
