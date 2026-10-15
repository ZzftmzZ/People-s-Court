/* People's Court — cena Three.js monocromática (fundo de partículas + martelo do hero).
   Pausa com a aba oculta / canvas fora da tela e é ignorada em dispositivos fracos. */
(function () {
    'use strict';
    var THREE = window.THREE;
    if (!THREE) return;

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var conn = navigator.connection || {};
    var weak = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) ||
               (navigator.deviceMemory && navigator.deviceMemory <= 2) || conn.saveData === true;
    var mobile = window.innerWidth < 768;
    var DPR = Math.min(window.devicePixelRatio || 1, mobile ? 1.5 : 2);

    function makeRenderer(canvas) {
        try {
            var r = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: !mobile, powerPreference: 'low-power' });
            r.setPixelRatio(DPR);
            return r;
        } catch (e) { return null; } // sem WebGL: página continua funcional
    }

    /* ── Fundo de partículas ── */
    function initBackground() {
        var canvas = document.getElementById('canvas-3d-bg');
        if (!canvas || weak) return;
        var renderer = makeRenderer(canvas);
        if (!renderer) return;

        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
        camera.position.z = 400;

        var COUNT = mobile ? 45 : 90;
        var pos = new Float32Array(COUNT * 3), vel = [];
        for (var i = 0; i < COUNT; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 800;
            pos[i * 3 + 1] = (Math.random() - 0.5) * 800;
            pos[i * 3 + 2] = (Math.random() - 0.5) * 400;
            vel.push([(Math.random() - 0.5) * 0.3, (Math.random() - 0.5) * 0.3]);
        }
        var geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        var mat = new THREE.PointsMaterial({ color: 0xffffff, size: 3, transparent: true, opacity: 0.55 });
        var points = new THREE.Points(geo, mat);
        scene.add(points);

        var mx = 0, my = 0, tx = 0, ty = 0;
        if (!mobile) document.addEventListener('pointermove', function (e) {
            tx = (e.clientX / window.innerWidth - 0.5) * 0.3;
            ty = (e.clientY / window.innerHeight - 0.5) * 0.3;
        }, { passive: true });

        function resize() {
            var w = window.innerWidth, h = window.innerHeight;
            camera.aspect = w / h; camera.updateProjectionMatrix();
            renderer.setSize(w, h, false);
        }
        resize();
        window.addEventListener('resize', resize);

        var running = !reduce, raf = 0;
        function draw() {
            for (var i = 0; i < COUNT; i++) {
                pos[i * 3] += vel[i][0]; pos[i * 3 + 1] += vel[i][1];
                if (pos[i * 3] < -400 || pos[i * 3] > 400) vel[i][0] *= -1;
                if (pos[i * 3 + 1] < -400 || pos[i * 3 + 1] > 400) vel[i][1] *= -1;
            }
            geo.attributes.position.needsUpdate = true;
            mx += (tx - mx) * 0.05; my += (ty - my) * 0.05;
            points.rotation.y += 0.001;
            scene.rotation.x = my; scene.rotation.z = mx * 0.3;
            renderer.render(scene, camera);
        }
        function loop() { raf = requestAnimationFrame(loop); draw(); }

        draw(); // 1 quadro estático (também cobre prefers-reduced-motion)
        if (running) loop();
        document.addEventListener('visibilitychange', function () {
            if (!running) return;
            if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } else if (!raf) loop();
        });
    }

    /* ── Martelo 3D do hero ── */
    function initHero() {
        var canvas = document.getElementById('hero-3d-object-canvas');
        if (!canvas) return;
        var renderer = makeRenderer(canvas);
        if (!renderer) { canvas.style.display = 'none'; return; }
        var SIZE = 180;
        renderer.setSize(SIZE, SIZE, false);

        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
        camera.position.z = 5;

        scene.add(new THREE.AmbientLight(0xffffff, 0.55));
        var key = new THREE.DirectionalLight(0xffffff, 1.4); key.position.set(4, 5, 5); scene.add(key);
        var rim = new THREE.PointLight(0xa1a1aa, 2, 40); rim.position.set(-5, -3, 4); scene.add(rim);

        var group = new THREE.Group();
        var head = new THREE.Mesh(
            new THREE.CylinderGeometry(0.5, 0.5, 1.6, 32),
            new THREE.MeshStandardMaterial({ color: 0xe4e4e7, metalness: 0.85, roughness: 0.28 })
        );
        head.rotation.z = Math.PI / 2;
        var handle = new THREE.Mesh(
            new THREE.CylinderGeometry(0.12, 0.16, 2.4, 32),
            new THREE.MeshStandardMaterial({ color: 0x52525b, metalness: 0.6, roughness: 0.4 })
        );
        handle.position.y = -1.2;
        group.add(head, handle);
        scene.add(group);

        var visible = true, raf = 0, t0 = performance.now();
        function draw(now) {
            var t = (now - t0) / 1000;
            group.rotation.y = t * 0.9;
            group.rotation.x = Math.sin(t) * 0.2;
            group.rotation.z = Math.cos(t) * 0.1;
            renderer.render(scene, camera);
        }
        function loop(now) { raf = requestAnimationFrame(loop); draw(now); }
        function sync() {
            var should = visible && !document.hidden && !reduce;
            if (should && !raf) raf = requestAnimationFrame(loop);
            if (!should && raf) { cancelAnimationFrame(raf); raf = 0; }
        }
        draw(performance.now());
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) { visible = es[0].isIntersecting; sync(); }).observe(canvas);
        }
        document.addEventListener('visibilitychange', sync);
        sync();
    }

    initBackground();
    initHero();
})();
