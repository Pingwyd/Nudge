import './style.css';

// ── Auto-update download links from latest GitHub release ────────
(async () => {
  try {
    const res = await fetch('https://api.github.com/repos/Pingwyd/Nudge/releases/latest');
    if (!res.ok) return;
    const data = await res.json();
    const exe = data.assets?.find((a) => a.name.endsWith('.exe'));
    if (!exe) return;
    const url = exe.browser_download_url;
    const version = data.tag_name?.replace(/^v/, '') || '';
    document.querySelectorAll('.btn-download').forEach((btn) => {
      btn.href = url;
      const label = btn.querySelector('.download-label');
      if (label && version) label.textContent = `Download v${version}`;
    });
  } catch (_) {}
})();

// ── Full-page glass-shine particles ──────────────────────────────
const canvas = document.getElementById('glow-bg');
const ctx = canvas.getContext('2d');
let particles = [];
let mouseX = -9999;
let mouseY = -9999;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

class Particle {
  constructor() {
    this.reset(true);
  }

  reset(initial = false) {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.size = Math.random() * 3 + 1;

    // Wandering velocity — each particle drifts on its own
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 0.6 + 0.15;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;

    // Wander: target offset for organic medium-radius drifting
    this.wanderAngle = Math.random() * Math.PI * 2;
    this.wanderStrength = 0.003 + Math.random() * 0.006;
    this.wanderRadius = 0.3 + Math.random() * 0.5;

    this.opacity = Math.random() * 0.55 + 0.15;
    this.baseOpacity = this.opacity;

    // Color: mix of warm orange and cool blue-cyan
    const roll = Math.random();
    if (roll < 0.45) {
      // Warm orange/amber
      this.r = 255;
      this.g = 160 + Math.random() * 60;
      this.b = 40 + Math.random() * 30;
    } else if (roll < 0.8) {
      // Cool blue-cyan
      this.r = 60 + Math.random() * 30;
      this.g = 170 + Math.random() * 40;
      this.b = 230 + Math.random() * 25;
    } else {
      // White glass sparkle
      this.r = 255;
      this.g = 255;
      this.b = 255;
      this.opacity *= 0.6;
      this.baseOpacity = this.opacity;
    }

    this.trail = [];
    this.trailLength = Math.floor(Math.random() * 4) + 2;

    if (!initial) {
      // Spawn from edge
      const edge = Math.floor(Math.random() * 4);
      if (edge === 0) { this.x = -10; this.y = Math.random() * canvas.height; }
      else if (edge === 1) { this.x = canvas.width + 10; this.y = Math.random() * canvas.height; }
      else if (edge === 2) { this.y = -10; this.x = Math.random() * canvas.width; }
      else { this.y = canvas.height + 10; this.x = Math.random() * canvas.width; }
    }
  }

  update() {
    // Store trail position
    this.trail.push({ x: this.x, y: this.y });
    if (this.trail.length > this.trailLength) this.trail.shift();

    // Organic wander — medium radius drifting
    this.wanderAngle += (Math.random() - 0.5) * this.wanderStrength * 10;
    this.vx += Math.cos(this.wanderAngle) * this.wanderRadius * 0.02;
    this.vy += Math.sin(this.wanderAngle) * this.wanderRadius * 0.02;

    // Dampen velocity so it stays in a medium range
    this.vx *= 0.995;
    this.vy *= 0.995;

    // Clamp speed
    const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
    const maxSpeed = 1.2;
    if (speed > maxSpeed) {
      this.vx = (this.vx / speed) * maxSpeed;
      this.vy = (this.vy / speed) * maxSpeed;
    }

    // Mouse attraction — glass shine follows cursor across the page
    const dx = mouseX - this.x;
    const dy = mouseY - this.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 350 && dist > 10) {
      const pull = (350 - dist) / 350;
      this.vx += (dx / dist) * pull * 0.3;
      this.vy += (dy / dist) * pull * 0.3;
      this.opacity = Math.min(this.baseOpacity + pull * 0.4, 1);
    } else {
      this.opacity += (this.baseOpacity - this.opacity) * 0.03;
    }

    this.x += this.vx;
    this.y += this.vy;

    // Wrap around edges with padding
    const pad = 60;
    if (this.x < -pad) this.x = canvas.width + pad;
    if (this.x > canvas.width + pad) this.x = -pad;
    if (this.y < -pad) this.y = canvas.height + pad;
    if (this.y > canvas.height + pad) this.y = -pad;
  }

  draw() {
    // Draw trail (glass shine streak)
    for (let i = 0; i < this.trail.length; i++) {
      const t = this.trail[i];
      const alpha = (i / this.trail.length) * this.opacity * 0.3;
      ctx.beginPath();
      ctx.arc(t.x, t.y, this.size * 0.6, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.r}, ${this.g}, ${this.b}, ${alpha})`;
      ctx.fill();
    }

    // Main particle
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${this.r}, ${this.g}, ${this.b}, ${this.opacity})`;
    ctx.fill();

    // Glow halo
    if (this.size > 1.5) {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
      const grad = ctx.createRadialGradient(
        this.x, this.y, 0,
        this.x, this.y, this.size * 3
      );
      grad.addColorStop(0, `rgba(${this.r}, ${this.g}, ${this.b}, ${this.opacity * 0.15})`);
      grad.addColorStop(1, `rgba(${this.r}, ${this.g}, ${this.b}, 0)`);
      ctx.fillStyle = grad;
      ctx.fill();
    }
  }
}

function initParticles() {
  // Enough particles to fill the whole page visibly
  const area = canvas.width * canvas.height;
  const count = Math.min(Math.floor(area / 5000), 200);
  particles = Array.from({ length: count }, () => new Particle());
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const p of particles) {
    p.update();
    p.draw();
  }
  requestAnimationFrame(animateParticles);
}

resizeCanvas();
initParticles();
animateParticles();

window.addEventListener('resize', () => {
  resizeCanvas();
  initParticles();
});

window.addEventListener('mousemove', (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
});

// ── Active nav link tracking ─────────────────────────────────────
const navLinksEl = document.querySelectorAll('.nav-links a[href^="#"]');
const sections = ['features', 'themes', 'how-it-works', 'download'].map((id) => ({
  id,
  el: document.getElementById(id),
}));

function updateActiveNav() {
  const scrollY = window.scrollY + 120;
  let current = '';

  for (const s of sections) {
    if (!s.el) continue;
    const top = s.el.offsetTop;
    const height = s.el.offsetHeight;
    if (scrollY >= top && scrollY < top + height) {
      current = s.id;
    }
  }

  navLinksEl.forEach((link) => {
    const href = link.getAttribute('href');
    if (href === `#${current}`) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

window.addEventListener('scroll', updateActiveNav, { passive: true });
updateActiveNav();

// ── Smooth anchor scrolling ──────────────────────────────────────
let scrollAnimation = null;

function smoothScrollTo(targetY, duration = 800) {
  if (scrollAnimation) cancelAnimationFrame(scrollAnimation);

  const startY = window.scrollY;
  const diff = targetY - startY;
  const startTime = performance.now();

  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out cubic
    const ease = 1 - Math.pow(1 - progress, 3);

    window.scrollTo(0, startY + diff * ease);

    if (progress < 1) {
      scrollAnimation = requestAnimationFrame(step);
    } else {
      scrollAnimation = null;
    }
  }

  scrollAnimation = requestAnimationFrame(step);
}

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', (e) => {
    const href = anchor.getAttribute('href');
    if (href === '#') return;
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      const navHeight = 64;
      const top = target.getBoundingClientRect().top + window.scrollY - navHeight;
      smoothScrollTo(top, 900);
    }
  });
});

// ── Nav scroll background ────────────────────────────────────────
const nav = document.getElementById('nav');

window.addEventListener('scroll', () => {
  if (window.scrollY > 50) {
    nav.style.background = 'rgba(10, 10, 10, 0.92)';
  } else {
    nav.style.background = 'rgba(10, 10, 10, 0.7)';
  }
}, { passive: true });

// ── Mobile nav toggle ────────────────────────────────────────────
const navToggle = document.getElementById('nav-toggle');
const navLinksContainer = document.querySelector('.nav-links');

navToggle.addEventListener('click', () => {
  navLinksContainer.classList.toggle('open');
});

navLinksContainer.querySelectorAll('a').forEach((a) => {
  a.addEventListener('click', () => {
    navLinksContainer.classList.remove('open');
  });
});

// ── Scroll reveal ────────────────────────────────────────────────
const revealElements = document.querySelectorAll('[data-reveal]');

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, i * 80);
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
);

revealElements.forEach((el) => revealObserver.observe(el));

// ── Mockup task hover interaction ────────────────────────────────
document.querySelectorAll('.mockup-task').forEach((task) => {
  task.addEventListener('mouseenter', () => {
    task.style.background = 'rgba(255, 255, 255, 0.08)';
  });
  task.addEventListener('mouseleave', () => {
    task.style.background = '';
  });
});

// ── Theme card glow on hover ─────────────────────────────────────
document.querySelectorAll('.theme-card').forEach((card) => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(79, 195, 247, 0.06), transparent 60%), linear-gradient(135deg, var(--glass-start), var(--glass-end))`;
  });
  card.addEventListener('mouseleave', () => {
    card.style.background = '';
  });
});

// ── Download modal ───────────────────────────────────────────────
const downloadModal = document.getElementById('download-modal');
const countdownEl = document.getElementById('modal-countdown');
const progressBar = document.getElementById('modal-progress-bar');
const modalClose = document.getElementById('modal-close');
let downloadUrl = '';
let countdownInterval = null;

document.querySelectorAll('.btn-download').forEach((btn) => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    downloadUrl = btn.href;
    openDownloadModal();
  });
});

function openDownloadModal() {
  let seconds = 5;
  countdownEl.textContent = seconds;
  progressBar.style.transition = 'none';
  progressBar.style.width = '0%';
  downloadModal.classList.add('open');

  // Trigger reflow then animate progress bar
  void progressBar.offsetWidth;
  progressBar.style.transition = 'width 5s linear';
  progressBar.style.width = '100%';

  countdownInterval = setInterval(() => {
    seconds--;
    countdownEl.textContent = seconds;
    if (seconds <= 0) {
      clearInterval(countdownInterval);
      triggerDownload();
      closeDownloadModal();
    }
  }, 1000);
}

function triggerDownload() {
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = '';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function closeDownloadModal() {
  downloadModal.classList.remove('open');
  if (countdownInterval) clearInterval(countdownInterval);
}

modalClose.addEventListener('click', closeDownloadModal);
downloadModal.addEventListener('click', (e) => {
  if (e.target === downloadModal) closeDownloadModal();
});
