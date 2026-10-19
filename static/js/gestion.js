(() => {
  "use strict";

  const navBouton = document.querySelector("[data-nav-bouton]");
  const nav = document.querySelector(".gestion-sidebar");
  const voile = document.querySelector("[data-nav-fermer]");
  const fermerNav = () => {
    if (!nav || !voile || !navBouton) return;
    nav.classList.remove("ouvert");
    voile.classList.remove("ouvert");
    navBouton.setAttribute("aria-expanded", "false");
    document.body.classList.remove("tiroir-ouvert");
    navBouton.focus();
  };
  if (navBouton && nav && voile) {
    navBouton.addEventListener("click", () => {
      const ouvert = nav.classList.toggle("ouvert");
      voile.classList.toggle("ouvert", ouvert);
      navBouton.setAttribute("aria-expanded", String(ouvert));
      document.body.classList.toggle("tiroir-ouvert", ouvert);
      if (ouvert) nav.querySelector("a")?.focus();
    });
    voile.addEventListener("click", fermerNav);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && nav.classList.contains("ouvert")) {
        fermerNav();
      }
    });
  }

  document.querySelectorAll("[data-confirm]").forEach((formulaire) => {
    formulaire.addEventListener("submit", (event) => {
      if (!window.confirm(formulaire.dataset.confirm)) event.preventDefault();
    });
  });

  const imageInput = document.querySelector("[data-image-form] input[type=file]");
  const imageCadre = document.querySelector("[data-image-cadre]");
  if (imageInput && imageCadre) {
    imageInput.addEventListener("change", () => {
      const fichier = imageInput.files?.[0];
      if (!fichier) return;
      if (!fichier.type.startsWith("image/")) {
        imageInput.setCustomValidity("Sélectionnez un fichier image.");
        imageInput.reportValidity();
        imageInput.setCustomValidity("");
        return;
      }
      imageCadre.replaceChildren();
      const image = document.createElement("img");
      image.alt = "Aperçu de l’image sélectionnée";
      image.src = URL.createObjectURL(fichier);
      image.onload = () => URL.revokeObjectURL(image.src);
      imageCadre.append(image);
    });
  }

  const selectReserv = document.querySelector('select[name="reserv"]');
  const resumeElement = document.getElementById("resume-reservations");
  if (selectReserv && resumeElement) {
    const resumes = JSON.parse(resumeElement.textContent);
    const sortie = {
      total: document.querySelector("[data-total]"),
      paye: document.querySelector("[data-paye]"),
      solde: document.querySelector("[data-solde]"),
    };
    const actualiserResume = () => {
      const donnees = resumes[selectReserv.value];
      if (!donnees) {
        Object.values(sortie).forEach((element) => {
          if (element) element.textContent = "—";
        });
        return;
      }
      const total = Number(donnees.total);
      const paye = Number(donnees.paye);
      if (sortie.total) sortie.total.textContent = `${total.toFixed(2)} Ar`;
      if (sortie.paye) sortie.paye.textContent = `${paye.toFixed(2)} Ar`;
      if (sortie.solde) sortie.solde.textContent = `${Math.max(total - paye, 0).toFixed(2)} Ar`;
    };
    selectReserv.addEventListener("change", actualiserResume);
    actualiserResume();
  }
})();
