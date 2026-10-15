/* People's Court — animações GSAP/ScrollTrigger + tilt 3D.
   Degrada com elegância: sem GSAP ou com prefers-reduced-motion, tudo fica visível e estático. */
(function () {
    'use strict';

    var root = document.documentElement;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function showAll() { root.classList.remove('pc-motion'); }

    if (reduce || typeof window.gsap === 'undefined') { showAll(); return; }

    var gsap = window.gsap;
    if (window.ScrollTrigger) gsap.registerPlugin(window.ScrollTrigger);

    // Elementos revelados no scroll (genérico: vale para qualquer página)
    var REVEAL = [
        '.hero-3d-inner > *', '.stat-card-3d', '.ai-banner-3d', '.cat-card-3d',
        '.page-container .card', '.page-container h2', '.page-container h3',
        '.footer-col', '.footer-bottom'
    ].join(',');

    var targets = Array.prototype.slice.call(document.querySelectorAll(REVEAL));
    targets.forEach(function (el) { el.setAttribute('data-pc-reveal', ''); });

    function done(el) {
        el.setAttribute('data-pc-done', '');
        gsap.set(el, { clearProps: 'opacity,visibility,transform' }); // devolve o hover/tilt ao CSS
    }

    function reveal(batch, delay) {
        gsap.to(batch, {
            autoAlpha: 1, y: 0, duration: 0.8, ease: 'power3.out',
            stagger: 0.08, delay: delay || 0, overwrite: 'auto',
            onComplete: function () { batch.forEach(done); }
        });
    }

    var hero = targets.filter(function (el) { return el.matches('.hero-3d-inner > *'); });
    var rest = targets.filter(function (el) { return hero.indexOf(el) === -1; });

    // Hero: entrada imediata, em cascata
    if (hero.length) reveal(hero, 0.1);

    // Resto: ao entrar na viewport (em lote)
    if (window.ScrollTrigger) {
        window.ScrollTrigger.batch(rest, {
            start: 'top 92%', once: true,
            onEnter: function (batch) { reveal(batch); }
        });
        // Parallax suave do hero ao rolar
        var heroSection = document.querySelector('.hero-3d');
        if (heroSection) {
            gsap.to('.hero-3d-inner', {
                yPercent: 12, ease: 'none',
                scrollTrigger: { trigger: heroSection, start: 'top top', end: 'bottom top', scrub: 0.6 }
            });
        }
        window.addEventListener('load', function () { window.ScrollTrigger.refresh(); });
    } else {
        reveal(rest);
    }

    // Segurança: nada fica invisível se algo falhar
    setTimeout(function () {
        targets.forEach(function (el) { if (!el.hasAttribute('data-pc-done') && el.getBoundingClientRect().top < window.innerHeight) done(el); });
    }, 4000);

    // ── Tilt 3D só em ponteiro fino (mouse), sem formulários ──
    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        var tiltEls = document.querySelectorAll('.card, .cat-card-3d, .stat-card-3d');
        Array.prototype.forEach.call(tiltEls, function (el) {
            if (el.querySelector('form, input, textarea, select')) return;
            el.classList.add('pc-tilt');
            var raf = 0, ev = null;
            function frame() {
                raf = 0;
                var r = el.getBoundingClientRect();
                var x = (ev.clientX - r.left) / r.width - 0.5;
                var y = (ev.clientY - r.top) / r.height - 0.5;
                el.style.setProperty('--pc-ry', (x * 8).toFixed(2) + 'deg');
                el.style.setProperty('--pc-rx', (-y * 8).toFixed(2) + 'deg');
            }
            el.addEventListener('pointermove', function (e) { ev = e; if (!raf) raf = requestAnimationFrame(frame); });
            el.addEventListener('pointerleave', function () {
                el.style.removeProperty('--pc-rx'); el.style.removeProperty('--pc-ry');
            });
        });
    }
})();
