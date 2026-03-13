window.SMS = window.SMS || {};

window.SMS.initCarousel = function initCarousel(id) {
  const root = document.getElementById(id);
  if (!root) return;
  const slides = Array.from(root.querySelectorAll(".carousel-slide"));
  if (!slides.length) return;
  let current = 0;

  function show(index) {
    slides.forEach((s, i) => {
      s.classList.toggle("active", i === index);
    });
  }

  function next(delta) {
    current = (current + delta + slides.length) % slides.length;
    show(current);
  }

  const prevBtn = root.querySelector(".carousel-control.prev");
  const nextBtn = root.querySelector(".carousel-control.next");
  if (prevBtn) prevBtn.addEventListener("click", () => next(-1));
  if (nextBtn) nextBtn.addEventListener("click", () => next(1));

  let timer = setInterval(() => next(1), 5000);
  root.addEventListener("mouseenter", () => clearInterval(timer));
  root.addEventListener("mouseleave", () => {
    timer = setInterval(() => next(1), 5000);
  });

  show(current);
};

