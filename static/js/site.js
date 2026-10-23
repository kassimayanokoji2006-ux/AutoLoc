(() => {
  "use strict";

  const menuBtn = document.querySelector("[data-menu-bouton]");
  const menu = document.querySelector("[data-menu]");
  const fermerMenu = () => {
    if (!menu || !menuBtn) return;
    menu.classList.remove("ouvert");
    menuBtn.setAttribute("aria-expanded", "false");
  };
  if (menuBtn && menu) {
    menuBtn.addEventListener("click", () => {
      const ouvert = menu.classList.toggle("ouvert");
      menuBtn.setAttribute("aria-expanded", String(ouvert));
    });
    document.addEventListener("click", (event) => {
      const clicDansMenu = menu.contains(event.target);
      const clicSurBouton = menuBtn.contains(event.target);
      if (!clicDansMenu && !clicSurBouton) fermerMenu();
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 760) fermerMenu();
    });
  }

  const panneau = document.querySelector("[data-filtres]");
  const ouvrirFiltres = document.querySelector("[data-filtres-bouton]");
  const fermerFiltres = document.querySelector("[data-filtres-fermer]");
  const basculerFiltres = (ouvert) => {
    if (!panneau) return;
    panneau.classList.toggle("ouvert", ouvert);
    if (ouvrirFiltres) ouvrirFiltres.setAttribute("aria-expanded", String(ouvert));
    document.body.classList.toggle("tiroir-ouvert", ouvert);
    if (ouvert && fermerFiltres) fermerFiltres.focus();
    if (!ouvert && ouvrirFiltres) ouvrirFiltres.focus();
  };
  if (ouvrirFiltres) ouvrirFiltres.addEventListener("click", () => basculerFiltres(true));
  if (fermerFiltres) fermerFiltres.addEventListener("click", () => basculerFiltres(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panneau && panneau.classList.contains("ouvert")) {
      basculerFiltres(false);
    }
  });

  document.querySelectorAll("[data-favori-url]").forEach((bouton) => {
    bouton.addEventListener("click", async () => {
      bouton.disabled = true;
      try {
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
        const reponse = await fetch(bouton.dataset.favoriUrl, {
          method: "POST",
          headers: { "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        });
        if (!reponse.ok) throw new Error("La mise à jour du favori a échoué.");
        const donnees = await reponse.json();
        bouton.classList.toggle("actif", donnees.favori);
        bouton.setAttribute("aria-pressed", String(donnees.favori));
        bouton.setAttribute("aria-label", donnees.favori ? "Retirer des favoris" : "Ajouter aux favoris");
      } catch {
        window.alert("Impossible de modifier ce favori. Réessayez.");
      } finally {
        bouton.disabled = false;
      }
    });
  });

  const formulaire = document.querySelector("[data-reservation]");
  if (formulaire) {
    const debut = formulaire.querySelector('[name="dat_deb"]');
    const fin = formulaire.querySelector('[name="dat_fin"]');
    const sortie = formulaire.querySelector("[data-prix-total]");
    const prixJour = Number(formulaire.dataset.prix);
    const mettreAJour = () => {
      if (!debut.value || !fin.value || !Number.isFinite(prixJour)) {
        sortie.textContent = "—";
        return;
      }
      const jours = Math.round((Date.parse(`${fin.value}T00:00:00`) - Date.parse(`${debut.value}T00:00:00`)) / 86400000);
      sortie.textContent = jours > 0 ? `${(jours * prixJour).toFixed(2)} Ar (${jours} jour${jours > 1 ? "s" : ""})` : "Choisissez une fin postérieure au début";
    };
    debut.addEventListener("change", mettreAJour);
    fin.addEventListener("change", mettreAJour);
  }
})();
