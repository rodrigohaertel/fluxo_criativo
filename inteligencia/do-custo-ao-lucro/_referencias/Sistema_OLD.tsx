import { useEffect } from "react";
import { Check, Monitor, ShieldCheck, Lock, ClipboardList, TrendingDown, Layers, Zap } from "lucide-react";
const rodrigoFoto = "https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Rodrigo%20Haertel.webp";
const sistemaPrintDesktop = "https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/desafio-print-produtos.webp";
const sistemaPrintMobile = "https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/sistema-print-mobile.webp";
const sistemaHeroImg    = "https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Sistema-Dashboard-BCG.webp";
const sistemaTabletImg  = "https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Sistema-Tablet.webp";

const Sistema = () => {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = "Software Dono 14% — Precificação e Lucro para Restaurantes";
    const meta = document.querySelector('meta[name="description"]');
    const prevDesc = meta?.getAttribute("content") ?? null;
    meta?.setAttribute(
      "content",
      "Precifique com margem real, monitore CMV em tempo real e tome decisões com números. R$ 97/mês, sem contrato.",
    );

    const root = document.querySelector(".sistema-page");
    if (!root) {
      return () => {
        document.title = prevTitle;
        if (prevDesc !== null) meta?.setAttribute("content", prevDesc);
      };
    }

    // Accordion FAQ
    const items = Array.from(root.querySelectorAll<HTMLElement>(".accordion-item"));
    const accordionHandlers: Array<() => void> = [];
    items.forEach((item) => {
      const header = item.querySelector<HTMLElement>(".accordion-header");
      if (!header) return;
      const onClick = () => {
        const isActive = item.classList.contains("active");
        items.forEach((other) => {
          other.classList.remove("active");
          const body = other.querySelector<HTMLElement>(".accordion-body");
          if (body) body.style.maxHeight = "";
          const icon = other.querySelector<HTMLElement>(".accordion-icon");
          if (icon) icon.textContent = "+";
        });
        if (!isActive) {
          item.classList.add("active");
          const body = item.querySelector<HTMLElement>(".accordion-body");
          if (body) body.style.maxHeight = body.scrollHeight + "px";
          const icon = item.querySelector<HTMLElement>(".accordion-icon");
          if (icon) icon.textContent = "−";
        }
      };
      header.addEventListener("click", onClick);
      accordionHandlers.push(() => header.removeEventListener("click", onClick));
    });

    // Tab pills
    const pills = Array.from(root.querySelectorAll<HTMLElement>(".tab-pill"));
    const pillHandlers: Array<() => void> = [];
    pills.forEach((tab) => {
      const onClick = () => {
        pills.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
      };
      tab.addEventListener("click", onClick);
      pillHandlers.push(() => tab.removeEventListener("click", onClick));
    });

    // Scroll animations
    const animEls = root.querySelectorAll(".anim-fade-up");
    const animObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            animObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    animEls.forEach((el) => animObserver.observe(el));

    // Count-up flash on urgência
    const numCards = root.querySelectorAll<HTMLElement>(".urgencia-num");
    let observed = false;
    const urgenciaSection = root.querySelector(".urgencia-section");
    let urgenciaObserver: IntersectionObserver | null = null;
    if (urgenciaSection && numCards.length) {
      urgenciaObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && !observed) {
              observed = true;
              numCards.forEach((el) => {
                el.classList.add("counting");
                window.setTimeout(() => el.classList.remove("counting"), 500);
              });
            }
          });
        },
        { threshold: 0.3 },
      );
      urgenciaObserver.observe(urgenciaSection);
    }

    // Sticky CTA — aparece após scroll de 80% do hero
    const stickyEl = document.getElementById("sp-sticky");
    const heroSection = root.querySelector(".hero") as HTMLElement | null;
    let stickyHandler: (() => void) | null = null;
    if (stickyEl && heroSection) {
      const onScroll = () => {
        const heroBottom = heroSection.getBoundingClientRect().bottom;
        if (heroBottom < 0) {
          stickyEl.classList.add("sp-sticky--visible");
        } else {
          stickyEl.classList.remove("sp-sticky--visible");
        }
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      stickyHandler = () => window.removeEventListener("scroll", onScroll);
    }

    return () => {
      accordionHandlers.forEach((off) => off());
      pillHandlers.forEach((off) => off());
      animObserver.disconnect();
      urgenciaObserver?.disconnect();
      stickyHandler?.();
      document.title = prevTitle;
      if (prevDesc !== null) meta?.setAttribute("content", prevDesc);
    };
  }, []);

  return (
    <>
      <style>{`/* Auto-generated from pagina-saas.html — scoped under .sistema-page */

    
    .sistema-page *, .sistema-page *::before, .sistema-page *::after { box-sizing: border-box; margin: 0; padding: 0; }
    .sistema-page { scroll-behavior: smooth; }
    .sistema-page {
      font-family: var(--font-b);
      background: var(--bg-dark)
        radial-gradient(ellipse 80% 60% at 60% -5%, hsla(36,55%,62%,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 60% 40% at 0% 80%, hsla(165,60%,30%,0.10) 0%, transparent 60%);
      color: var(--text-light);
      line-height: 1.7;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }
    .sistema-page img { max-width: 100%; display: block; }
    .sistema-page a { text-decoration: none; color: inherit; }
    .sistema-page ul { list-style: none; }

    
    .sistema-page {
      --primary:       hsl(36,55%,62%);
      --primary-100:   hsl(38,70%,78%);
      --primary-dark:  hsl(34,60%,48%);
      --primary-light: hsla(36,55%,62%,0.12);
      --primary-glow:  hsla(36,70%,60%,0.18);
      --grad-gold:     linear-gradient(180deg, hsl(38,70%,78%) 0%, hsl(36,55%,62%) 100%);
      --grad-text:     linear-gradient(135deg, hsl(38,70%,78%) 0%, hsl(36,55%,62%) 50%, hsl(34,60%,48%) 100%);
      --shad-gold:     0 14px 40px -14px hsla(36,55%,62%,0.45);
      --green:         hsl(145,50%,50%);
      --red:           hsl(4,70%,55%);
      --bg-ultra:      hsl(165,60%,5%);
      --bg-dark:       hsl(165,50%,8%);
      --bg-dark-alt:   hsl(165,45%,11%);
      --bg-card:       hsl(165,40%,14%);
      --bg-card-hover: hsl(165,38%,17%);
      --bg-light:      #F5EFE1;
      --text-white:    hsl(38,40%,94%);
      --text-light:    hsl(38,35%,92%);
      --text-muted:    hsla(38,35%,92%,0.62);
      --text-dark:     #1C1C1C;
      --text-dark-muted: #4A4A4A;
      --border-subtle: hsl(165,30%,20%);
      --border-primary: hsla(36,55%,62%,0.32);
      --radius:        12px;
      --radius-lg:     20px;
      --radius-pill:   50px;
      --font-h:        'Fraunces', Georgia, serif;
      --font-b:        'Inter', sans-serif;
      --transition:    0.3s ease;
      --ease:          cubic-bezier(0.22,1,0.36,1);
    }

    
    .sistema-page h1, .sistema-page h2, .sistema-page h3 { font-family: var(--font-h); line-height: 1.1; font-weight: 700; }
    .sistema-page h1 { font-size: clamp(2.6rem, 5.5vw, 4.4rem); }
    .sistema-page h2 { font-size: clamp(2rem, 4vw, 3.4rem); }
    .sistema-page h3 { font-size: clamp(1.15rem, 2.5vw, 1.5rem); }

    .sistema-page .eyebrow {
      display: inline-flex; align-items: center; gap: 8px;
      font-family: var(--font-b); font-size: 0.72rem; font-weight: 600;
      letter-spacing: 0.14em; text-transform: uppercase; color: var(--primary);
      padding: 7px 14px 7px 12px;
      border: 1px solid var(--border-primary);
      border-radius: var(--radius-pill); margin-bottom: 24px;
      background: linear-gradient(180deg, hsla(36,55%,62%,0.10), hsla(36,55%,62%,0.04));
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
    }
    .sistema-page .eyebrow-dot {
      width: 6px; height: 6px; border-radius: 50%; background: var(--primary);
      box-shadow: 0 0 8px var(--primary);
      animation: sp-dot-pulse 2.5s ease-in-out infinite;
      display: inline-block;
    }
    @keyframes sp-dot-pulse {
      0%,100% { box-shadow: 0 0 8px var(--primary); opacity:1; }
      50%      { box-shadow: 0 0 14px var(--primary); opacity:.85; }
    }
    .sistema-page .eyebrow--dark { color: var(--primary-dark); border-color: rgba(196,105,26,0.4); }
    .sistema-page .eyebrow--dark .eyebrow-dot { background: var(--primary-dark); }

    
    .sistema-page .container { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
    .sistema-page .container--narrow { max-width: 720px; margin: 0 auto; padding: 0 24px; }
    .sistema-page .grid-2 { display: grid; grid-template-columns: 1fr; gap: 24px; }
    .sistema-page .grid-3 { display: grid; grid-template-columns: 1fr; gap: 24px; }
    .sistema-page .grid-4 { display: grid; grid-template-columns: repeat(2,1fr); gap: 20px; }
    @media(min-width:640px){ .sistema-page .grid-3 { grid-template-columns: repeat(3,1fr); } }
    @media(min-width:768px){ .sistema-page .grid-2 { grid-template-columns: 1fr 1fr; } .sistema-page .grid-4 { grid-template-columns: repeat(4,1fr); } }

    
    .sistema-page .section-ultra { background: var(--bg-ultra); padding: 96px 0; position: relative; overflow: hidden; }
    .sistema-page .section-dark { background: var(--bg-dark);  padding: 96px 0; position: relative; overflow: hidden; }
    .sistema-page .section-alt { background: var(--bg-dark-alt); padding: 96px 0; position: relative; overflow: hidden; }
    .sistema-page .section-dark > .container, .sistema-page .section-alt > .container, .sistema-page .section-ultra > .container { position: relative; z-index: 1; }
    .sistema-page .section-light { background: var(--bg-light); padding: 96px 0; color: var(--text-dark); }
    .sistema-page .section-light h2 { color: var(--text-dark); }
    .sistema-page .section-light .section-header p { color: var(--text-dark-muted); }

    
    .sistema-page .glow-top::before {
      content: ''; position: absolute; top: -120px; left: 50%; transform: translateX(-50%);
      width: 900px; height: 600px;
      background: radial-gradient(ellipse at center, hsla(36,55%,62%,0.15) 0%, transparent 65%);
      pointer-events: none; z-index: 0;
    }
    .sistema-page .glow-side::after {
      content: ''; position: absolute; top: 30%; left: -200px;
      width: 500px; height: 500px;
      background: radial-gradient(circle, hsla(36,55%,62%,0.10) 0%, transparent 65%);
      pointer-events: none; z-index: 0;
    }
    .sistema-page .section-ultra > .container, .sistema-page .section-dark > .container, .sistema-page .section-alt > .container, .sistema-page .section-ultra > .container--narrow, .sistema-page .section-dark > .container--narrow { position: relative; z-index: 1; }

    
    .sistema-page .btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 10px;
      font-family: var(--font-b); font-weight: 700; font-size: 1rem;
      border-radius: var(--radius-pill); border: none; cursor: pointer;
      transition: var(--transition); text-align: center; text-decoration: none;
    }
    .sistema-page .btn-primary {
      background: var(--grad-gold);
      color: hsl(165,60%,8%);
      padding: 20px 52px;
      font-size: 1.1rem;
      box-shadow: var(--shad-gold);
      position: relative; overflow: hidden;
    }
    .sistema-page .btn-primary::before {
      content: '';
      position: absolute; top: 0; left: -100%;
      width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, hsla(38,90%,95%,.45), transparent);
      transition: left .7s var(--ease);
      pointer-events: none;
    }
    .sistema-page .btn-primary:hover::before { left: 100%; }
    .sistema-page .btn-primary:hover {
      transform: translateY(-2px);
      filter: brightness(1.05);
      box-shadow: 0 20px 48px -12px hsla(36,70%,50%,0.6);
    }

    .sistema-page .trust-row {
      display: flex; flex-wrap: wrap; gap: 20px; font-size: 0.82rem;
      color: var(--text-muted); margin-top: 20px; justify-content: center;
    }
    .sistema-page .trust-item { display: flex; align-items: center; gap: 6px; }
    .sistema-page .trust-item::before { content: '✓'; color: var(--primary); font-weight: 700; }

    
    .sistema-page .section-header { text-align: center; margin-bottom: 16px; }
    .sistema-page .section-header h2 { margin-bottom: 16px; }
    .sistema-page .section-header p { font-size: 1.05rem; color: var(--text-muted); max-width: 580px; margin: 0 auto; line-height: 1.65; }

    
    .sistema-page .hero {
      min-height: 100vh; display: flex;
      flex-direction: column; justify-content: center; padding: 80px 0 60px;
      position: relative; overflow: hidden;
      background:
        linear-gradient(180deg, hsla(165,60%,6%,0.80) 0%, hsla(165,50%,8%,0.94) 100%),
        url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Sistema-hero.webp') center/cover no-repeat;
    }
    .sistema-page .hero::before {
      content: ''; position: absolute; top: -150px; left: 50%; transform: translateX(-50%);
      width: 1000px; height: 700px;
      background: radial-gradient(ellipse at center top, hsla(36,55%,62%,0.15) 0%, transparent 60%);
      pointer-events: none;
    }
    .sistema-page .hero-inner {
      position: relative; z-index: 1; text-align: center;
      display: grid; grid-template-columns: 1fr; gap: 48px;
    }
    .sistema-page .hero-left { display: flex; flex-direction: column; align-items: center; }
    .sistema-page .hero-right { display: flex; align-items: center; justify-content: center; }
    @media(min-width: 860px) {
      .sistema-page .hero-inner { grid-template-columns: 1.1fr 1fr; align-items: center; text-align: left; }
      .sistema-page .hero-left { align-items: flex-start; }
      .sistema-page .hero-right { justify-content: flex-end; }
      .sistema-page .hero h1 { text-align: left; margin-left: 0; }
      .sistema-page .hero-sub { text-align: left; margin-left: 0; }
      .sistema-page .hero-stat-anchor { align-items: flex-start; }
      .sistema-page .hero-stat-label { text-align: left; }
      .sistema-page .hero-cta-wrap { text-align: left; }
      .sistema-page .trust-row { justify-content: flex-start; }
      .sistema-page .mockup-wrap { margin-top: 0; max-width: 100%; }
    }

    
    .sistema-page .hero-logo {
      display: inline-block;
      margin-bottom: 40px;
    }
    .sistema-page .hero-logo-placeholder {
      display: inline-flex; align-items: center; gap: 12px;
      background: rgba(255,255,255,0.04);
      border: 1px dashed rgba(255,255,255,0.15);
      border-radius: var(--radius-pill);
      padding: 10px 24px;
      font-family: var(--font-h);
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-muted);
    }
    .sistema-page .hero-logo-dot {
      width: 10px; height: 10px; border-radius: 50%; background: var(--primary);
    }

    .sistema-page .hero h1 { max-width: 820px; margin: 0 auto 24px; color: var(--text-white); font-weight: 900; letter-spacing: -0.02em; }
    .sistema-page .hero h1 em { font-style: italic; color: var(--primary); }
    .sistema-page .hero-sub { font-size: clamp(1rem, 2vw, 1.25rem); color: var(--text-muted); max-width: 560px; margin: 0 auto; line-height: 1.65; }

    .sistema-page .hero-cta-wrap { text-align: center; margin-top: 40px; }

    
    .sistema-page .mockup-wrap { margin-top: 64px; max-width: 880px; margin-left: auto; margin-right: auto; }
    .sistema-page .browser-frame {
      background: #111; border-radius: 12px; overflow: hidden;
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 24px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06);
    }
    .sistema-page .browser-bar {
      background: #1A1A1A; padding: 12px 16px; display: flex; align-items: center;
      gap: 8px; border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .sistema-page .browser-dot { width: 12px; height: 12px; border-radius: 50%; }
    .sistema-page .browser-dot:nth-child(1) {background:#FF5F57;} .sistema-page .browser-dot:nth-child(2) {background:#FEBC2E;} .sistema-page .browser-dot:nth-child(3) {background:#28C840;}
    .sistema-page .browser-url { flex:1; background: rgba(255,255,255,0.06); border-radius:6px; padding:5px 12px; font-size:0.75rem; color:rgba(255,255,255,0.35); font-family: var(--font-b); margin-left:8px; }
    .sistema-page .browser-content { background: #0F1A14; padding: 20px; }
    .sistema-page .dash-preview { display: grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }
    .sistema-page .dash-stat { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07); border-radius:8px; padding:12px 16px; }
    .sistema-page .dash-stat-label { font-size:0.65rem; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px; font-family:var(--font-b); }
    .sistema-page .dash-stat-value { font-family:var(--font-h); font-size:1.4rem; font-weight:700; background: var(--grad-text); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .sistema-page .dash-stat-sub { font-size:0.6rem; color:rgba(255,255,255,0.3); margin-top:2px; font-family:var(--font-b); }
    .sistema-page .dash-main { grid-column:span 3; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:16px; }
    .sistema-page .dash-table-row { display:grid; grid-template-columns:2fr 1fr 1fr 1fr; gap:8px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.65rem; font-family:var(--font-b); }
    .sistema-page .dash-table-row.header { color:rgba(255,255,255,0.3); text-transform:uppercase; letter-spacing:0.08em; }
    .sistema-page .dash-table-row:not(.header) { color:rgba(255,255,255,0.65); }
    .sistema-page .d-green { color:var(--green) !important; } .sistema-page .d-orange { color:var(--primary) !important; } .sistema-page .d-red { color:var(--red) !important; }

    
    .sistema-page .video-frame {
      position:relative; aspect-ratio:16/9;
      background: linear-gradient(135deg, #0F2920 0%, #0B1F18 100%);
      border-radius:var(--radius-lg); overflow:hidden; border:1px solid var(--border-subtle);
      max-width:800px; margin:48px auto 0;
    }
    .sistema-page .video-frame::before { content:''; position:absolute; inset:0; background:radial-gradient(ellipse at center, rgba(232,135,30,0.08) 0%, transparent 60%); }
    .sistema-page .play-btn {
      position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
      width:80px; height:80px; border-radius:50%; background:var(--primary);
      display:flex; align-items:center; justify-content:center;
      box-shadow:0 0 40px rgba(232,135,30,0.4); transition:var(--transition); z-index:2;
    }
    .sistema-page .play-btn:hover { transform:translate(-50%,-50%) scale(1.1); box-shadow:0 0 60px rgba(232,135,30,0.6); }
    .sistema-page .play-icon { width:0; height:0; border-style:solid; border-width:14px 0 14px 24px; border-color:transparent transparent transparent #fff; margin-left:5px; }
    .sistema-page .video-label { position:absolute; bottom:20px; left:50%; transform:translateX(-50%); font-size:0.82rem; color:var(--text-muted); white-space:nowrap; }
    .sistema-page .tab-pills { display:flex; flex-wrap:wrap; justify-content:center; gap:10px; margin-top:28px; }
    .sistema-page .tab-pill { padding:8px 18px; border-radius:var(--radius-pill); font-size:0.8rem; font-weight:500; color:var(--text-muted); border:1px solid var(--border-subtle); cursor:pointer; transition:var(--transition); }
    .sistema-page .tab-pill.active, .sistema-page .tab-pill:hover { background:var(--primary-light); border-color:var(--border-primary); color:var(--primary); }

    
    .sistema-page .photo-card {
      position: relative;
      border-radius: var(--radius);
      overflow: hidden;
      min-height: 280px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      cursor: default;
    }
    .sistema-page .photo-card-bg {
      position: absolute;
      inset: 0;
      background-size: cover;
      background-position: center;
      transition: transform 0.5s ease;
    }
    .sistema-page .photo-card:hover .photo-card-bg { transform: scale(1.04); }
    .sistema-page .photo-card-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(to top, rgba(7,15,12,0.92) 0%, rgba(7,15,12,0.4) 55%, rgba(7,15,12,0.1) 100%);
    }
    .sistema-page .photo-card-content {
      position: relative;
      z-index: 1;
      padding: 24px;
    }
    .sistema-page .photo-card h3 {
      font-family: var(--font-h);
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--text-white);
      margin-bottom: 6px;
    }
    .sistema-page .photo-card p {
      font-size: 0.88rem;
      color: rgba(240,237,230,0.75);
      line-height: 1.5;
    }
    
    .sistema-page .photo-card-bg--burguer {
      background:
        radial-gradient(ellipse at 75% 20%, rgba(180,85,15,0.55) 0%, transparent 55%),
        radial-gradient(ellipse at 20% 80%, rgba(100,40,5,0.3) 0%, transparent 45%),
        linear-gradient(155deg, #0D0400 0%, #2A0F00 35%, #4A1C00 65%, #1C0900 100%);
    }
    .sistema-page .photo-card-bg--pizza {
      background:
        radial-gradient(ellipse at 72% 22%, rgba(160,35,25,0.55) 0%, transparent 55%),
        radial-gradient(ellipse at 22% 78%, rgba(90,15,10,0.3) 0%, transparent 45%),
        linear-gradient(155deg, #080100 0%, #220707 35%, #440E0E 65%, #160404 100%);
    }
    .sistema-page .photo-card-bg--rest {
      background:
        radial-gradient(ellipse at 72% 22%, rgba(30,110,55,0.45) 0%, transparent 55%),
        radial-gradient(ellipse at 22% 78%, rgba(15,65,30,0.25) 0%, transparent 45%),
        linear-gradient(155deg, #020602 0%, #08180B 35%, #10301A 65%, #050E07 100%);
    }
    .sistema-page .photo-card-bg--cafe {
      background:
        radial-gradient(ellipse at 72% 22%, rgba(140,65,15,0.5) 0%, transparent 55%),
        radial-gradient(ellipse at 22% 78%, rgba(85,35,5,0.3) 0%, transparent 45%),
        linear-gradient(155deg, #080300 0%, #200E00 35%, #3C1A00 65%, #140800 100%);
    }
    
    .sistema-page .photo-card-bg::before {
      content: '';
      position: absolute;
      inset: 0;
      background-image: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 3px,
        rgba(255,255,255,0.012) 3px,
        rgba(255,255,255,0.012) 4px
      );
      pointer-events: none;
    }
    
    .sistema-page .photo-card-bg::after {
      content: '';
      position: absolute;
      top: -40px; right: -40px;
      width: 160px; height: 160px;
      border-radius: 50%;
      filter: blur(50px);
      opacity: 0.35;
      pointer-events: none;
    }
    .sistema-page .photo-card-bg--burguer::after { background: #C06A10; }
    .sistema-page .photo-card-bg--pizza::after { background: #B82020; }
    .sistema-page .photo-card-bg--rest::after { background: #1A6630; }
    .sistema-page .photo-card-bg--cafe::after { background: #8B4A10; }
    
    .sistema-page .photo-card-tag {
      position: absolute;
      top: 20px; left: 20px;
      z-index: 2;
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(240,237,230,0.45);
      font-family: var(--font-b);
      border: 1px solid rgba(240,237,230,0.15);
      padding: 4px 10px;
      border-radius: 4px;
      backdrop-filter: blur(4px);
    }
    
    .sistema-page .photo-card-question {
      font-size: 0.82rem;
      font-style: italic;
      color: rgba(232,135,30,0.85);
      margin-bottom: 8px;
      line-height: 1.45;
    }
    
    .sistema-page .para-quem-nao {
      margin-top: 56px;
      padding-top: 40px;
      border-top: 1px solid var(--border-subtle);
      display: flex;
      align-items: flex-start;
      gap: 48px;
      flex-wrap: wrap;
    }
    .sistema-page .para-quem-nao-label {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-muted);
      margin-bottom: 14px;
    }
    .sistema-page .para-quem-sim { flex: 1; min-width: 240px; }
    .sistema-page .para-quem-nao-col { flex: 1; min-width: 240px; }
    .sistema-page .pq-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 10px;
      font-size: 0.88rem;
      color: var(--text-muted);
      line-height: 1.5;
    }
    .sistema-page .pq-item-icon-sim { color: var(--primary); font-weight: 700; flex-shrink: 0; }
    .sistema-page .pq-item-icon-nao { color: rgba(240,237,230,0.25); font-weight: 700; flex-shrink: 0; }

    
    .sistema-page .devices-section { padding: 80px 0 96px; background: var(--bg-ultra); position: relative; overflow: hidden; }
    .sistema-page .devices-wrap {
      display: flex;
      align-items: flex-end;
      justify-content: center;
      gap: 24px;
      margin-top: 56px;
      padding: 0 24px;
    }
    
    .sistema-page .device-desktop {
      flex: 1;
      max-width: 600px;
    }
    .sistema-page .device-desktop .device-frame {
      background: #1A1A1A; border-radius: 10px;
      border: 2px solid rgba(255,255,255,0.1);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      overflow: hidden;
    }
    .sistema-page .device-desktop .device-bar {
      background: #111; padding: 8px 12px; display: flex; align-items: center; gap: 6px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .sistema-page .device-desktop .device-bar .device-dot { width: 8px; height: 8px; border-radius: 50%; }
    .sistema-page .device-screen {
      background: #0F1A14;
      aspect-ratio: 16/10;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 8px;
      color: rgba(255,255,255,0.2);
      font-size: 0.75rem;
      font-family: var(--font-b);
      text-align: center;
      padding: 16px;
    }
    .sistema-page .device-screen-icon { font-size: 1.5rem; opacity: 0.3; margin-bottom: 4px; }
    .sistema-page .device-desktop .device-stand {
      width: 40%;
      height: 16px;
      background: #1A1A1A;
      margin: 0 auto;
      border-radius: 0 0 6px 6px;
      border: 2px solid rgba(255,255,255,0.08);
      border-top: none;
    }
    .sistema-page .device-desktop .device-base {
      width: 60%;
      height: 6px;
      background: #111;
      margin: 0 auto;
      border-radius: 3px;
    }
    
    .sistema-page .device-tablet {
      flex-shrink: 0;
      width: 200px;
    }
    .sistema-page .device-tablet .device-frame {
      background: #1A1A1A;
      border-radius: 12px;
      border: 2px solid rgba(255,255,255,0.1);
      box-shadow: 0 16px 40px rgba(0,0,0,0.4);
      overflow: hidden;
      padding: 8px;
    }
    .sistema-page .device-tablet .device-screen-inner {
      background: #0F1A14;
      border-radius: 6px;
      aspect-ratio: 3/4;
      display: flex; align-items: center; justify-content: center;
      flex-direction: column; gap: 6px;
      color: rgba(255,255,255,0.2); font-size: 0.65rem; font-family: var(--font-b); text-align: center;
    }
    
    .sistema-page .device-phone {
      flex-shrink: 0;
      width: 120px;
    }
    .sistema-page .device-phone .device-frame {
      background: #1A1A1A;
      border-radius: 20px;
      border: 2px solid rgba(255,255,255,0.12);
      box-shadow: 0 12px 32px rgba(0,0,0,0.4);
      overflow: hidden;
      padding: 6px;
    }
    .sistema-page .device-phone .device-notch {
      width: 40%;
      height: 6px;
      background: #111;
      border-radius: 3px;
      margin: 4px auto 6px;
    }
    .sistema-page .device-phone .device-screen-inner {
      background: #0F1A14;
      border-radius: 14px;
      aspect-ratio: 9/19;
      display: flex; align-items: center; justify-content: center;
      flex-direction: column; gap: 4px;
      color: rgba(255,255,255,0.2); font-size: 0.6rem; font-family: var(--font-b); text-align: center;
      padding: 8px;
    }
    @media(max-width:640px){
      .sistema-page .devices-wrap { flex-direction: column; align-items: center; gap: 32px; }
      .sistema-page .device-tablet, .sistema-page .device-phone { width: 160px; }
    }

    
    .sistema-page .feat-grid { display: grid; grid-template-columns: 1fr; gap: 20px; margin-top: 56px; }
    @media(min-width:640px){ .sistema-page .feat-grid { grid-template-columns: 1fr 1fr; } }
    @media(min-width:900px){ .sistema-page .feat-grid { grid-template-columns: 1fr 1fr 1fr; } }
    .sistema-page .feat-card {
      background: #fff; border: 1px solid rgba(0,0,0,0.07); border-radius: var(--radius);
      padding: 28px 24px; transition: var(--transition); position: relative; overflow: hidden;
    }
    .sistema-page .feat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--primary); transform:scaleX(0); transform-origin:left; transition:var(--transition); }
    .sistema-page .feat-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.1); transform: translateY(-3px); }
    .sistema-page .feat-card:hover::before { transform: scaleX(1); }
    .sistema-page .feat-num { display:inline-flex; align-items:center; justify-content:center; width:44px; height:44px; border-radius:10px; background:rgba(232,135,30,0.1); border:1px solid rgba(232,135,30,0.25); font-family:var(--font-h); font-weight:700; font-size:1rem; color:var(--primary); margin-bottom:16px; }
    .sistema-page .feat-card h3 { font-family:var(--font-h); font-size:1.05rem; font-weight:700; color:var(--text-dark); margin-bottom:8px; }
    .sistema-page .feat-card p { font-size:0.9rem; color:var(--text-dark-muted); line-height:1.6; }
    .sistema-page .feat-card .tag { display:inline-block; margin-top:12px; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary); background:rgba(232,135,30,0.1); padding:3px 10px; border-radius:4px; }

    
    .sistema-page .feat-card--dark {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
    }
    .sistema-page .feat-card--dark h3 { color: var(--text-light); }
    .sistema-page .feat-card--dark p { color: var(--text-muted); }
    .sistema-page .feat-card--dark .feat-num { background: var(--primary-light); border-color: var(--border-primary); color: var(--primary); }
    .sistema-page .feat-card--dark .tag { background: rgba(232,135,30,0.15); color: var(--primary); }
    .sistema-page .feat-card--dark:hover { background: var(--bg-card-hover); border-color: var(--border-primary); transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px var(--border-primary); }
    .sistema-page .feat-card--dark::before { background: var(--primary); }

    
    .sistema-page .feat-card--highlight {
      background: rgba(232,135,30,0.07);
      border: 1px solid var(--border-primary);
    }
    .sistema-page .feat-card--highlight h3 { color: var(--primary); }
    .sistema-page .feat-card--highlight p { color: var(--text-muted); }
    .sistema-page .feat-card--highlight .feat-num { background: var(--primary); color: #fff; border-color: transparent; }
    .sistema-page .feat-card--highlight .tag { background: rgba(232,135,30,0.15); color: var(--primary); }

    
    .sistema-page .bonus-card {
      max-width: 680px; margin: 48px auto 0;
      background: linear-gradient(160deg, hsla(36,55%,62%,0.10) 0%, hsla(36,55%,62%,0.04) 100%);
      border: 2px solid var(--border-primary);
      border-radius: var(--radius-lg); padding: 48px 40px; text-align: center; position: relative;
      box-shadow: 0 0 80px -24px hsla(36,55%,62%,0.30), inset 0 1px 0 hsla(36,55%,62%,0.18);
    }
    .sistema-page .bonus-badge { position:absolute; top:-16px; left:50%; transform:translateX(-50%); background:var(--primary); color:#fff; font-size:0.72rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:6px 20px; border-radius:var(--radius-pill); white-space:nowrap; }
    .sistema-page .bonus-card h3 { font-family:var(--font-h); font-size:clamp(1.4rem,3vw,2rem); font-weight:700; color:var(--text-light); margin-bottom:16px; line-height:1.25; }
    .sistema-page .bonus-card p { color:var(--text-muted); font-size:1rem; line-height:1.6; max-width:520px; margin:0 auto; }

    
    .sistema-page .depo-grid { display:grid; grid-template-columns:1fr; gap:20px; margin-top:48px; }
    @media(min-width:640px){ .sistema-page .depo-grid { grid-template-columns: repeat(3,1fr); } }
    .sistema-page .depo-card {
      background: var(--bg-card); border: 1px solid var(--border-subtle);
      border-radius: var(--radius); padding: 28px 24px;
      display: flex; flex-direction: column; gap: 16px;
    }
    .sistema-page .depo-card--placeholder { border-style: dashed; opacity: 0.6; align-items: center; justify-content: center; min-height: 200px; text-align: center; }
    .sistema-page .depo-placeholder-icon { font-size: 1.8rem; margin-bottom: 8px; }
    .sistema-page .depo-placeholder-label { font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; }

    
    .sistema-page .antes-depois-section { background: var(--bg-ultra); padding: 96px 0; position: relative; overflow: hidden; }
    .sistema-page .antes-depois-section::before {
      content: ''; position: absolute; top: -100px; left: 50%; transform: translateX(-50%);
      width: 800px; height: 600px;
      background: radial-gradient(ellipse at center, hsla(36,55%,62%,0.11) 0%, transparent 65%);
      pointer-events: none;
    }
    .sistema-page .antes-depois-inner { position: relative; z-index: 1; }
    .sistema-page .antes-depois-headline {
      text-align: center;
      margin-bottom: 64px;
    }
    .sistema-page .antes-depois-headline h2 {
      font-size: clamp(2.4rem, 5vw, 4rem);
      line-height: 1.05;
      color: var(--text-white);
    }
    .sistema-page .antes-depois-headline h2 em { font-style: italic; color: var(--primary); }
    .sistema-page .antes-depois-headline p {
      font-size: 1.1rem;
      color: var(--text-muted);
      max-width: 500px;
      margin: 20px auto 0;
      line-height: 1.65;
    }

    .sistema-page .ad-grid { display: grid; grid-template-columns: 1fr; gap: 3px; }
    @media(min-width:768px){ .sistema-page .ad-grid { grid-template-columns: 1fr 1fr; gap: 4px; } }

    .sistema-page .ad-col {
      padding: 48px 40px;
      display: flex;
      flex-direction: column;
      gap: 0;
    }
    .sistema-page .ad-col--antes {
      background: rgba(239,68,68,0.07);
      border: 1px solid rgba(239,68,68,0.2);
      border-radius: var(--radius) 0 0 var(--radius);
    }
    .sistema-page .ad-col--depois {
      background: rgba(34,197,94,0.07);
      border: 1px solid rgba(34,197,94,0.2);
      border-radius: 0 var(--radius) var(--radius) 0;
    }
    @media(max-width:767px){
      .sistema-page .ad-col--antes { border-radius: var(--radius) var(--radius) 0 0; }
      .sistema-page .ad-col--depois { border-radius: 0 0 var(--radius) var(--radius); }
    }
    .sistema-page .ad-col-label {
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase;
      margin-bottom: 28px;
    }
    .sistema-page .ad-col--antes .ad-col-label { color: var(--red); }
    .sistema-page .ad-col--depois .ad-col-label { color: var(--green); }

    .sistema-page .ad-item {
      padding: 18px 0;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
    .sistema-page .ad-item:last-child { border-bottom: none; }
    .sistema-page .ad-icon {
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.85rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;
    }
    .sistema-page .ad-col--antes .ad-icon { background: rgba(239,68,68,0.15); color: var(--red); }
    .sistema-page .ad-col--depois .ad-icon { background: rgba(34,197,94,0.15); color: var(--green); }
    .sistema-page .ad-item-text {
      flex: 1;
    }
    .sistema-page .ad-item-text strong {
      display: block;
      font-family: var(--font-h);
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-light);
      margin-bottom: 4px;
      line-height: 1.3;
    }
    .sistema-page .ad-item-text span {
      font-size: 0.88rem;
      color: var(--text-muted);
      line-height: 1.5;
    }

    .sistema-page .ad-anchor {
      text-align: center;
      margin-top: 56px;
      position: relative;
      z-index: 1;
    }
    .sistema-page .ad-anchor-quote {
      font-family: var(--font-h);
      font-style: italic;
      font-size: clamp(1.4rem, 3vw, 2rem);
      color: var(--text-white);
      line-height: 1.3;
    }
    .sistema-page .ad-anchor-quote em { color: var(--primary); font-style: italic; }
    .sistema-page .ad-anchor-sub { font-size: 1rem; color: var(--text-muted); margin-top: 12px; }

    
    .sistema-page .offer-box {
      background: hsla(165,45%,11%,0.55);
      border: 1px solid var(--border-primary);
      backdrop-filter: blur(20px) saturate(140%);
      -webkit-backdrop-filter: blur(20px) saturate(140%);
      border-radius: var(--radius-lg); padding: 48px 40px; max-width: 700px; margin: 0 auto;
      box-shadow: 0 4px 24px hsla(0,0%,0%,0.3), inset 0 1px 0 hsla(38,70%,78%,0.08);
    }
    .sistema-page .entregavel-list { margin: 32px 0; }
    .sistema-page .entregavel-item { display:flex; align-items:flex-start; gap:12px; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.06); font-size:0.97rem; color:var(--text-muted); }
    .sistema-page .entregavel-item:last-child { border-bottom: none; }
    .sistema-page .entregavel-check { color:var(--green); font-weight:700; flex-shrink:0; margin-top:2px; }
    .sistema-page .ent-icon-circle {
      flex-shrink: 0; margin-top: 4px;
      width: 24px; height: 24px; border-radius: 50%;
      background: var(--grad-gold);
      display: flex; align-items: center; justify-content: center;
    }
    .sistema-page .price-display { text-align:center; padding:32px 0 24px; }
    .sistema-page .price-per { font-size:0.85rem; color:var(--text-muted); margin-bottom:4px; }
    .sistema-page .price-main { font-family:var(--font-h); font-size:clamp(3.5rem,7vw,5.5rem); font-weight:900; line-height:1; background: var(--grad-text); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .sistema-page .price-period { font-size:1.1rem; color:var(--text-muted); margin-top:4px; }
    .sistema-page .price-day { font-size:0.88rem; color:var(--text-muted); margin-top:8px; }
    .sistema-page .garantia-box { border:1px solid var(--border-primary); background: hsla(36,55%,62%,0.06); border-radius:var(--radius); padding:24px 28px; margin-top:32px; display:flex; gap:16px; align-items:flex-start; }
    .sistema-page .garantia-icon { flex-shrink:0; width:40px; height:40px; border-radius:50%; background: hsla(36,55%,62%,0.15); border:1px solid var(--border-primary); display:flex; align-items:center; justify-content:center; margin-top:2px; }
    .sistema-page .garantia-box h4 { font-family:var(--font-h); color:var(--text-light); margin-bottom:6px; font-size:1rem; }
    .sistema-page .garantia-box p { font-size:0.88rem; color:var(--text-muted); line-height:1.6; }

    
    .sistema-page .autoridade-grid { display:grid; grid-template-columns:1fr; gap:48px; align-items:start; margin-top:56px; }
    @media(min-width:768px){ .sistema-page .autoridade-grid { grid-template-columns: 280px 1fr; } }
    .sistema-page .autor-foto-wrap { display:flex; flex-direction:column; align-items:center; gap:24px; }
    .sistema-page .autor-foto-placeholder { width:220px; height:280px; border-radius:var(--radius); background:rgba(255,255,255,0.05); border:2px dashed var(--border-subtle); display:flex; align-items:center; justify-content:center; flex-direction:column; gap:8px; color:var(--text-muted); font-size:0.8rem; }
    .sistema-page .autor-foto-placeholder span { font-size:2.5rem; }
    .sistema-page .autoridade-emblema { background:var(--primary-light); border:1px solid var(--border-primary); border-radius:var(--radius); padding:20px 24px; text-align:center; width:100%; }
    .sistema-page .emblema-stat { font-family:var(--font-h); font-size:2rem; font-weight:900; color:var(--primary); line-height:1; }
    .sistema-page .emblema-label { font-size:0.78rem; color:var(--text-muted); margin-top:4px; line-height:1.4; }
    .sistema-page .autor-nome { font-family:var(--font-h); font-size:clamp(1.6rem,3vw,2.2rem); font-weight:700; color:var(--text-light); margin-bottom:8px; }
    .sistema-page .autor-especialidade { font-size:0.88rem; text-transform:uppercase; letter-spacing:0.1em; font-weight:600; color:var(--primary); margin-bottom:20px; }
    .sistema-page .autor-bio { color:var(--text-muted); font-size:1rem; line-height:1.75; margin-bottom:16px; }
    .sistema-page .autor-badges { display:flex; flex-wrap:wrap; gap:8px; margin-top:20px; }
    .sistema-page .autor-badge { display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.1); border-radius:var(--radius-pill); padding:6px 14px; font-size:0.8rem; color:var(--text-muted); font-weight:500; }
    .sistema-page .autor-badge::before { content:'✦'; color:var(--primary); font-size:0.65rem; }

    
    .sistema-page .comp-section { background: var(--bg-ultra); padding: 96px 0; position: relative; overflow: hidden; }
    .sistema-page .comp-header { text-align: center; margin-bottom: 56px; position: relative; z-index: 1; }
    .sistema-page .comp-header h2 { color: var(--text-white); margin-bottom: 16px; }
    .sistema-page .comp-header p { color: var(--text-muted); max-width: 520px; margin: 0 auto; font-size: 1.05rem; line-height: 1.65; }

    .sistema-page .comp-table {
      max-width: 800px;
      margin: 0 auto;
      position: relative;
      z-index: 1;
    }
    .sistema-page .comp-table-header {
      display: grid;
      grid-template-columns: 1fr 80px 80px;
      gap: 12px;
      padding: 16px 24px;
      margin-bottom: 8px;
    }
    .sistema-page .comp-table-header span { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; }
    .sistema-page .comp-table-header .col-sem { color: var(--red); text-align: center; }
    .sistema-page .comp-table-header .col-com { color: var(--green); text-align: center; }

    .sistema-page .comp-row {
      display: grid;
      grid-template-columns: 1fr 80px 80px;
      gap: 12px;
      align-items: center;
      padding: 16px 24px;
      border-radius: 8px;
      transition: var(--transition);
      border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .sistema-page .comp-row:last-child { border-bottom: none; }
    .sistema-page .comp-row:hover { background: rgba(255,255,255,0.03); }
    .sistema-page .comp-row-label { font-size: 0.97rem; color: var(--text-muted); line-height: 1.4; }
    .sistema-page .comp-row-label strong { display: block; color: var(--text-light); font-family: var(--font-h); font-size: 1.05rem; margin-bottom: 2px; }
    .sistema-page .comp-cell { text-align: center; font-size: 1.2rem; font-weight: 700; }
    .sistema-page .comp-cell--sem { color: var(--red); }
    .sistema-page .comp-cell--com { color: var(--primary); }

    
    .sistema-page .accordion-item { border-bottom: 1px solid var(--border-subtle); }
    .sistema-page .accordion-item:first-child { border-top: 1px solid var(--border-subtle); }
    .sistema-page .accordion-header { display:flex; justify-content:space-between; align-items:center; padding:22px 0; cursor:pointer; font-family:var(--font-h); font-weight:700; font-size:1.05rem; color:var(--text-light); gap:16px; user-select:none; }
    .sistema-page .accordion-icon { width:30px; height:30px; min-width:30px; border-radius:50%; background:var(--primary-light); border:1px solid var(--border-primary); display:flex; align-items:center; justify-content:center; font-size:1.3rem; color:var(--primary); flex-shrink:0; font-weight:300; line-height:1; transition:var(--transition); }
    .sistema-page .accordion-item.active .accordion-icon { background:var(--primary); color:#fff; border-color:transparent; }
    .sistema-page .accordion-item.active .accordion-header { color:var(--primary); }
    .sistema-page .accordion-body { max-height:0; overflow:hidden; transition:max-height 0.35s ease; }
    .sistema-page .accordion-body-inner { padding:0 0 24px; font-size:0.97rem; color:var(--text-muted); line-height:1.75; }

    
    .sistema-page .cta-final {
      background: var(--bg-ultra); padding: 120px 0; text-align: center;
      position: relative; overflow: hidden;
    }
    .sistema-page .cta-final::before {
      content: ''; position: absolute; top: -100px; left: 50%; transform: translateX(-50%);
      width: 800px; height: 600px;
      background: radial-gradient(ellipse at center, rgba(232,135,30,0.16) 0%, transparent 65%);
      pointer-events: none;
    }
    .sistema-page .cta-final > .container { position: relative; z-index: 1; }
    .sistema-page .cta-final h2 { max-width: 680px; margin: 0 auto 24px; color: var(--text-white); }
    .sistema-page .cta-final h2 em { font-style: italic; color: var(--primary); }
    .sistema-page .cta-final p { max-width: 480px; margin: 0 auto; color: var(--text-muted); font-size: 1.1rem; line-height: 1.65; }
    .sistema-page .cta-final-filosofia { font-family: var(--font-h); font-style: italic; font-size: clamp(1.1rem,2.5vw,1.5rem); color: var(--primary); margin-top: 56px; line-height: 1.45; }

    
    .sistema-page .footer { background: var(--bg-ultra); border-top: 1px solid var(--border-subtle); padding: 40px 0; text-align: center; color: var(--text-muted); font-size: 0.82rem; }
    .sistema-page .footer a { color: var(--primary); }
    .sistema-page .footer-links { display:flex; flex-wrap:wrap; gap:20px; justify-content:center; margin-top:12px; }

    
    @media(max-width:640px){
      .sistema-page .section-ultra, .sistema-page .section-dark, .sistema-page .section-alt, .sistema-page .section-light, .sistema-page .antes-depois-section, .sistema-page .comp-section, .sistema-page .devices-section { padding: 72px 0; }
      .sistema-page .hero { padding: 60px 0 48px; min-height: auto; }
      .sistema-page .offer-box { padding: 32px 20px; }
      .sistema-page .bonus-card { padding: 40px 24px; }
      .sistema-page .comp-row { grid-template-columns: 1fr 52px 52px; padding: 14px 16px; }
      .sistema-page .ad-col { padding: 32px 24px; }
      .sistema-page .dash-preview { grid-template-columns: 1fr 1fr; }
      .sistema-page .dash-stat:nth-child(3) { display: none; }
    }

    
    .sistema-page .metodo-section { background: var(--bg-ultra); padding: 96px 0; position: relative; overflow: hidden; }
    .sistema-page .metodo-section::before {
      content: '';
      position: absolute;
      top: -60px; left: 50%; transform: translateX(-50%);
      width: 600px; height: 600px;
      background: radial-gradient(circle, rgba(232,135,30,0.06) 0%, transparent 70%);
      pointer-events: none;
    }
    .sistema-page .metodo-title-block { text-align: center; margin-bottom: 64px; }
    .sistema-page .metodo-name {
      font-family: var(--font-h);
      font-size: clamp(2rem, 4vw, 3rem);
      font-weight: 700;
      color: var(--text-light);
      letter-spacing: -0.02em;
      line-height: 1.1;
      margin-bottom: 12px;
    }
    .sistema-page .metodo-name span { color: var(--primary); }
    .sistema-page .metodo-tagline {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-muted);
      letter-spacing: 0.04em;
    }
    .sistema-page .metodo-tagline .tl-word { color: var(--text-light); }
    .sistema-page .metodo-tagline .tl-arrow {
      color: var(--primary);
      font-size: 1.1rem;
      transition: transform 0.3s ease;
    }
    .sistema-page .metodo-tagline:hover .tl-arrow { transform: translateX(4px); }

    .sistema-page .metodo-steps {
      display: grid;
      grid-template-columns: 1fr auto 1fr auto 1fr;
      align-items: stretch;
      gap: 0 16px;
    }
    .sistema-page .metodo-connector { align-self: center; }
    .sistema-page .metodo-step {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius);
      padding: 36px 28px 28px;
      position: relative;
      transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease, background 0.35s ease;
      cursor: default;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .sistema-page .step-desc { flex: 1; margin-bottom: 24px; }
    
    .sistema-page .metodo-step::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: var(--primary);
      transform: scaleX(0);
      transform-origin: left;
      transition: transform 0.4s ease;
    }
    
    .sistema-page .metodo-step::after {
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(ellipse at 50% 120%, rgba(232,135,30,0.1) 0%, transparent 65%);
      opacity: 0;
      transition: opacity 0.4s ease;
      pointer-events: none;
    }
    .sistema-page .metodo-step:hover {
      transform: translateY(-8px);
      border-color: rgba(232,135,30,0.45);
      box-shadow: 0 16px 48px rgba(0,0,0,0.35), 0 0 0 1px rgba(232,135,30,0.15);
      background: var(--bg-card-hover);
    }
    .sistema-page .metodo-step:hover::before { transform: scaleX(1); }
    .sistema-page .metodo-step:hover::after { opacity: 1; }

    .sistema-page .step-num {
      font-family: var(--font-h);
      font-size: 3.5rem;
      font-weight: 700;
      line-height: 1;
      color: rgba(240,237,230,0.07);
      position: absolute;
      top: 16px; right: 20px;
      transition: color 0.35s ease;
      pointer-events: none;
    }
    .sistema-page .metodo-step:hover .step-num { color: rgba(232,135,30,0.18); }

    .sistema-page .step-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px; height: 36px;
      border-radius: 50%;
      background: var(--primary-light);
      border: 1px solid var(--border-primary);
      color: var(--primary);
      font-size: 0.8rem;
      font-weight: 700;
      margin-bottom: 20px;
      transition: background 0.35s ease, color 0.35s ease;
    }
    .sistema-page .metodo-step:hover .step-badge {
      background: var(--primary);
      color: #fff;
      border-color: transparent;
    }
    .sistema-page .step-title {
      font-family: var(--font-h);
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--text-light);
      margin-bottom: 12px;
      transition: color 0.35s ease;
    }
    .sistema-page .metodo-step:hover .step-title { color: var(--primary); }
    .sistema-page .step-desc {
      font-size: 0.9rem;
      color: var(--text-muted);
      line-height: 1.65;
      margin-bottom: 20px;
    }
    .sistema-page .step-result {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--primary);
      background: rgba(232,135,30,0.1);
      border: 1px solid rgba(232,135,30,0.2);
      padding: 4px 12px;
      border-radius: 4px;
      transition: background 0.35s ease, border-color 0.35s ease;
    }
    .sistema-page .metodo-step:hover .step-result {
      background: rgba(232,135,30,0.2);
      border-color: rgba(232,135,30,0.45);
    }

    
    .sistema-page .metodo-connector {
      display: flex;
      align-items: center;
      justify-content: center;
      padding-top: 60px;
    }
    .sistema-page .metodo-connector-inner {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      color: rgba(232,135,30,0.35);
      transition: color 0.4s ease;
    }
    .sistema-page .metodo-connector-line {
      width: 2px;
      height: 40px;
      background: currentColor;
      border-radius: 2px;
    }
    .sistema-page .metodo-connector-arrow {
      font-size: 1rem;
      line-height: 1;
      animation: pulse-down 2s ease-in-out infinite;
    }
    @keyframes pulse-down {
      0%, 100% { transform: translateY(0); opacity: 0.35; }
      50%       { transform: translateY(4px); opacity: 0.7; }
    }

    .sistema-page .metodo-footer {
      margin-top: 56px;
      text-align: center;
      border-top: 1px solid var(--border-subtle);
      padding-top: 40px;
    }
    .sistema-page .metodo-footer p {
      font-family: var(--font-h);
      font-size: clamp(1rem, 2vw, 1.2rem);
      font-style: italic;
      color: var(--text-muted);
    }
    .sistema-page .metodo-footer em { color: var(--primary); font-style: normal; }

    @media (max-width: 768px) {
      .sistema-page .metodo-steps {
        grid-template-columns: 1fr;
        gap: 0;
      }
      .sistema-page .metodo-connector { padding-top: 0; padding: 12px 0; transform: rotate(0deg); }
      .sistema-page .metodo-connector-line { width: 40px; height: 2px; }
    }

    
    .sistema-page .decorado-section {
      background: var(--bg-dark);
      padding: 80px 0;
      position: relative;
    }
    .sistema-page .decorado-section::before {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(to bottom, transparent 0%, rgba(232,135,30,0.03) 50%, transparent 100%);
      pointer-events: none;
    }
    .sistema-page .decorado-inner {
      max-width: 680px;
      margin: 0 auto;
      text-align: center;
      position: relative;
      z-index: 1;
    }
    .sistema-page .decorado-eyebrow {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--primary);
      margin-bottom: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }
    .sistema-page .decorado-eyebrow::before, .sistema-page .decorado-eyebrow::after {
      content: '';
      display: block;
      width: 40px;
      height: 1px;
      background: rgba(232,135,30,0.4);
    }
    .sistema-page .decorado-lines {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }
    .sistema-page .decorado-line {
      font-family: var(--font-h);
      font-size: clamp(1.1rem, 2.5vw, 1.4rem);
      font-weight: 400;
      font-style: italic;
      color: var(--text-muted);
      line-height: 1.55;
      transition: color 0.3s ease;
    }
    .sistema-page .decorado-line em {
      color: var(--text-light);
      font-style: normal;
      font-weight: 600;
    }
    .sistema-page .decorado-line:hover { color: var(--text-light); }
    .sistema-page .decorado-mantra {
      margin-top: 40px;
      font-family: var(--font-h);
      font-size: 1rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--primary);
    }

    
    .sistema-page .urgencia-section {
      background: var(--bg-ultra);
      padding: 96px 0;
      position: relative;
      overflow: hidden;
    }
    .sistema-page .urgencia-section::before {
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(ellipse at 50% 100%, hsla(4,70%,40%,0.07) 0%, transparent 65%);
      pointer-events: none;
    }
    .sistema-page .urgencia-header { text-align: center; margin-bottom: 64px; }
    .sistema-page .urgencia-header h2 { margin-bottom: 12px; }
    .sistema-page .urgencia-header p { color: var(--text-muted); font-size: 0.95rem; }

    
    .sistema-page .urgencia-calc {
      display: grid;
      grid-template-columns: 1fr auto 1fr auto 1fr;
      align-items: center;
      gap: 0 12px;
      margin-bottom: 56px;
    }
    .sistema-page .urgencia-card {
      border-radius: var(--radius);
      padding: 32px 28px;
      position: relative;
      overflow: hidden;
      border: 1px solid transparent;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .sistema-page .urgencia-card:hover { transform: translateY(-4px); }
    .sistema-page .urgencia-card::before {
      content: '';
      position: absolute;
      inset: 0;
      opacity: 0.06;
      background-image: repeating-linear-gradient(
        -45deg,
        transparent, transparent 6px,
        rgba(255,255,255,1) 6px, rgba(255,255,255,1) 7px
      );
    }
    
    .sistema-page .urgencia-card--1 {
      background: linear-gradient(145deg, #1A1000 0%, #2E1E00 50%, #3D2800 100%);
      border-color: rgba(200,140,0,0.3);
      box-shadow: 0 4px 32px rgba(200,140,0,0.08);
    }
    .sistema-page .urgencia-card--1:hover { box-shadow: 0 12px 48px rgba(200,140,0,0.15); }
    .sistema-page .urgencia-card--1 .urgencia-tag { color: #C89000; border-color: rgba(200,140,0,0.3); }
    .sistema-page .urgencia-card--1 .urgencia-num { color: #FFB800; }
    .sistema-page .urgencia-card--1 .urgencia-label { color: rgba(240,237,230,0.75); }
    
    .sistema-page .urgencia-card--2 {
      background: linear-gradient(145deg, #1A0A00 0%, #32180A 50%, #4A2210 100%);
      border-color: rgba(232,135,30,0.35);
      box-shadow: 0 4px 32px rgba(232,135,30,0.08);
    }
    .sistema-page .urgencia-card--2:hover { box-shadow: 0 12px 48px rgba(232,135,30,0.18); }
    .sistema-page .urgencia-card--2 .urgencia-tag { color: var(--primary); border-color: rgba(232,135,30,0.35); }
    .sistema-page .urgencia-card--2 .urgencia-num { color: var(--primary); }
    .sistema-page .urgencia-card--2 .urgencia-label { color: rgba(240,237,230,0.8); }
    
    .sistema-page .urgencia-card--3 {
      background: linear-gradient(145deg, #150300 0%, #2E0A08 50%, #460F0C 100%);
      border-color: rgba(210,60,40,0.35);
      box-shadow: 0 4px 32px rgba(210,60,40,0.08);
    }
    .sistema-page .urgencia-card--3:hover { box-shadow: 0 12px 48px rgba(210,60,40,0.2); }
    .sistema-page .urgencia-card--3 .urgencia-tag { color: #E05040; border-color: rgba(210,60,40,0.35); }
    .sistema-page .urgencia-card--3 .urgencia-num { color: #FF5040; }
    .sistema-page .urgencia-card--3 .urgencia-label { color: rgba(240,237,230,0.8); }

    .sistema-page .urgencia-tag {
      display: inline-block;
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      border: 1px solid;
      padding: 3px 10px;
      border-radius: 4px;
      margin-bottom: 20px;
      position: relative;
      z-index: 1;
    }
    .sistema-page .urgencia-num {
      font-family: var(--font-h);
      font-size: clamp(2.2rem, 4vw, 3rem);
      font-weight: 700;
      line-height: 1;
      margin-bottom: 10px;
      position: relative;
      z-index: 1;
      
      animation: none;
    }
    .sistema-page .urgencia-num.counting { animation: flash-in 0.4s ease forwards; }
    @keyframes flash-in {
      from { opacity: 0.3; transform: scale(0.92); }
      to   { opacity: 1;   transform: scale(1); }
    }
    .sistema-page .urgencia-label {
      font-size: 0.88rem;
      line-height: 1.5;
      position: relative;
      z-index: 1;
      margin-bottom: 16px;
    }
    .sistema-page .urgencia-detail {
      font-size: 0.78rem;
      color: rgba(240,237,230,0.35);
      line-height: 1.6;
      position: relative;
      z-index: 1;
      border-top: 1px solid rgba(255,255,255,0.06);
      padding-top: 14px;
      margin-top: 4px;
    }

    
    .sistema-page .urgencia-connector {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      font-family: var(--font-h);
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--primary);
      line-height: 1.1;
      text-align: center;
      padding: 0 4px;
      animation: pulse-glow 2.5s ease-in-out infinite;
    }
    .sistema-page .urgencia-connector span {
      font-family: var(--font-b);
      font-size: 0.65rem;
      font-weight: 400;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.6; }
      50%       { opacity: 1; }
    }

    
    .sistema-page .urgencia-resolve {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius);
      overflow: hidden;
      margin-bottom: 40px;
    }
    .sistema-page .urgencia-resolve-col {
      flex: 1;
      padding: 32px 36px;
      text-align: center;
    }
    .sistema-page .urgencia-resolve-col--win { background: rgba(10,25,15,0.8); }
    .sistema-page .urgencia-resolve-col--lose { background: rgba(30,8,5,0.6); }
    .sistema-page .urgencia-resolve-label {
      display: block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-bottom: 12px;
    }
    .sistema-page .urgencia-resolve-col--win  .urgencia-resolve-label { color: #5DBB7A; }
    .sistema-page .urgencia-resolve-col--lose .urgencia-resolve-label { color: #E05040; }
    .sistema-page .urgencia-resolve-price {
      font-family: var(--font-h);
      font-size: clamp(1.8rem, 3vw, 2.4rem);
      font-weight: 700;
      color: #5DBB7A;
      line-height: 1;
    }
    .sistema-page .urgencia-resolve-price span { font-size: 1rem; color: rgba(93,187,122,0.6); }
    .sistema-page .urgencia-resolve-loss {
      font-family: var(--font-h);
      font-size: clamp(1.8rem, 3vw, 2.4rem);
      font-weight: 700;
      color: #FF5040;
      line-height: 1;
      text-decoration: line-through;
      text-decoration-color: rgba(255,80,64,0.4);
    }
    .sistema-page .urgencia-resolve-loss span { font-size: 1rem; color: rgba(255,80,64,0.6); }
    .sistema-page .urgencia-resolve-sublabel {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 8px;
    }
    .sistema-page .urgencia-vs {
      padding: 0 24px;
      font-family: var(--font-h);
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-muted);
      flex-shrink: 0;
    }
    .sistema-page .urgencia-cta-wrap { text-align: center; }
    .sistema-page .urgencia-footnote {
      font-size: 0.72rem;
      color: rgba(240,237,230,0.25);
      margin-top: 16px;
      max-width: 520px;
      margin-left: auto;
      margin-right: auto;
      line-height: 1.6;
    }

    @media (max-width: 768px) {
      .sistema-page .urgencia-calc {
        grid-template-columns: 1fr;
        gap: 14px 0;
      }
      .sistema-page .urgencia-card {
        padding: 24px 22px;
      }
      .sistema-page .urgencia-num {
        font-size: clamp(2.4rem, 9vw, 3rem);
      }
      .sistema-page .urgencia-label {
        font-size: 0.92rem;
      }
      .sistema-page .urgencia-detail {
        font-size: 0.78rem;
      }
      .sistema-page .urgencia-connector {
        flex-direction: row;
        gap: 10px;
        padding: 6px 0;
        font-size: 1.05rem;
      }
      .sistema-page .urgencia-connector span {
        font-size: 0.7rem;
      }
      .sistema-page .urgencia-resolve { flex-direction: column; }
      .sistema-page .urgencia-resolve-col { padding: 22px 20px; }
      .sistema-page .urgencia-vs { padding: 10px 0; }
    }

    
    
    @keyframes shimmer {
      0%   { background-position: -600px 0; }
      100% { background-position:  600px 0; }
    }
    .sistema-page .placeholder-shimmer {
      background: linear-gradient(90deg,
        rgba(255,255,255,0.04) 25%,
        rgba(255,255,255,0.08) 50%,
        rgba(255,255,255,0.04) 75%
      );
      background-size: 600px 100%;
      animation: shimmer 2.4s infinite linear;
    }

    
    .sistema-page .depo-card--placeholder {
      border-style: solid !important;
      border-color: var(--border-subtle) !important;
      opacity: 1 !important;
      min-height: 220px;
      display: flex !important;
      flex-direction: column;
      gap: 0;
      overflow: hidden;
      padding: 0 !important;
    }
    .sistema-page .depo-placeholder-header {
      height: 80px;
      background: linear-gradient(90deg,
        rgba(255,255,255,0.04) 25%,
        rgba(255,255,255,0.07) 50%,
        rgba(255,255,255,0.04) 75%
      );
      background-size: 600px 100%;
      animation: shimmer 2.4s infinite linear;
      border-bottom: 1px solid var(--border-subtle);
      flex-shrink: 0;
    }
    .sistema-page .depo-placeholder-body {
      flex: 1;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .sistema-page .depo-placeholder-line {
      height: 10px;
      border-radius: 5px;
      background: linear-gradient(90deg,
        rgba(255,255,255,0.05) 25%,
        rgba(255,255,255,0.09) 50%,
        rgba(255,255,255,0.05) 75%
      );
      background-size: 600px 100%;
      animation: shimmer 2.4s infinite linear;
    }
    .sistema-page .depo-placeholder-line:nth-child(1) { width: 90%; animation-delay: 0s; }
    .sistema-page .depo-placeholder-line:nth-child(2) { width: 75%; animation-delay: 0.15s; }
    .sistema-page .depo-placeholder-line:nth-child(3) { width: 55%; animation-delay: 0.3s; }
    .sistema-page .depo-placeholder-avatar {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: auto;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }
    .sistema-page .depo-placeholder-circle {
      width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
      background: linear-gradient(90deg,
        rgba(255,255,255,0.06) 25%,
        rgba(255,255,255,0.1) 50%,
        rgba(255,255,255,0.06) 75%
      );
      background-size: 600px 100%;
      animation: shimmer 2.4s infinite linear;
    }
    .sistema-page .depo-placeholder-name {
      height: 8px; width: 80px; border-radius: 4px;
      background: linear-gradient(90deg,
        rgba(255,255,255,0.05) 25%,
        rgba(255,255,255,0.09) 50%,
        rgba(255,255,255,0.05) 75%
      );
      background-size: 600px 100%;
      animation: shimmer 2.4s infinite linear;
    }

    
    .sistema-page .device-screen-placeholder {
      width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center;
      flex-direction: column; gap: 12px;
    }
    .sistema-page .device-screen-placeholder-bar {
      height: 8px; border-radius: 4px;
      background: rgba(255,255,255,0.06);
    }
    .sistema-page .device-screen-placeholder-bar--w90 { width: 90%; }
    .sistema-page .device-screen-placeholder-bar--w70 { width: 70%; }
    .sistema-page .device-screen-placeholder-bar--w50 { width: 50%; }
    .sistema-page .device-screen-placeholder-rect {
      width: 85%; height: 40%; border-radius: 6px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.07);
    }

    
    .sistema-page .autor-foto-placeholder {
      width: 220px; height: 280px;
      border-radius: var(--radius);
      background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.03) 100%);
      border: 1px solid var(--border-subtle) !important;
      border-style: solid !important;
      display: flex; align-items: flex-end; justify-content: center;
      overflow: hidden; position: relative;
    }
    .sistema-page .autor-foto-silhouette {
      width: 90px; height: 130px;
      background: rgba(255,255,255,0.06);
      border-radius: 50px 50px 0 0;
      margin-bottom: 0;
      position: absolute;
      bottom: 0;
      left: 50%; transform: translateX(-50%);
    }
    .sistema-page .autor-foto-silhouette::before {
      content: '';
      position: absolute;
      top: -28px; left: 50%; transform: translateX(-50%);
      width: 48px; height: 48px; border-radius: 50%;
      background: rgba(255,255,255,0.07);
    }

    
    .sistema-page .hero-logo-placeholder {
      border-style: solid !important;
      border-color: rgba(232,135,30,0.2) !important;
      background: rgba(232,135,30,0.06) !important;
    }

    
    .sistema-page .anim-fade-up {
      opacity: 0;
      transform: translateY(28px);
      transition: opacity 0.6s ease, transform 0.6s ease;
    }
    .sistema-page .anim-fade-up.is-visible {
      opacity: 1;
      transform: translateY(0);
    }
    
    .sistema-page .anim-delay-1 { transition-delay: 0.1s; }
    .sistema-page .anim-delay-2 { transition-delay: 0.2s; }
    .sistema-page .anim-delay-3 { transition-delay: 0.3s; }
    .sistema-page .anim-delay-4 { transition-delay: 0.4s; }
    .sistema-page .anim-delay-5 { transition-delay: 0.5s; }

    
    .sistema-page .cta-final {
      background: var(--bg-ultra);
      padding: 140px 0 120px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }
    
    .sistema-page .cta-final::before {
      content: '';
      position: absolute;
      top: -80px; left: 50%; transform: translateX(-50%);
      width: 1100px; height: 700px;
      background:
        radial-gradient(ellipse at 35% 50%, hsla(36,55%,62%,0.13) 0%, transparent 55%),
        radial-gradient(ellipse at 65% 50%, hsla(165,60%,30%,0.10) 0%, transparent 55%);
      pointer-events: none;
    }
    
    .sistema-page .cta-final::after {
      content: '';
      position: absolute;
      inset: 0;
      background-image: radial-gradient(circle, hsla(36,55%,62%,0.12) 1px, transparent 1px);
      background-size: 40px 40px;
      mask-image: radial-gradient(ellipse at 50% 50%, black 0%, transparent 70%);
      -webkit-mask-image: radial-gradient(ellipse at 50% 50%, black 0%, transparent 70%);
      pointer-events: none;
    }
    .sistema-page .cta-final > .container { position: relative; z-index: 1; }
    
    .sistema-page .cta-final h2 {
      max-width: 820px;
      margin: 0 auto 28px;
      color: var(--text-white);
      font-size: clamp(2.4rem, 5.5vw, 4.8rem);
      letter-spacing: -0.025em;
      line-height: 1.05;
    }
    .sistema-page .cta-final h2 em { font-style: italic; color: var(--primary); }
    .sistema-page .cta-final p { max-width: 480px; margin: 0 auto; color: var(--text-muted); font-size: 1.1rem; line-height: 1.65; }
    
    .sistema-page .cta-final-divider {
      width: 48px; height: 2px;
      background: linear-gradient(90deg, transparent, var(--primary), transparent);
      margin: 40px auto;
    }
    
    .sistema-page .cta-final-filosofia {
      font-family: var(--font-h);
      font-style: italic;
      font-size: clamp(1.2rem, 2.5vw, 1.6rem);
      color: var(--primary);
      margin-top: 72px;
      line-height: 1.45;
      position: relative;
      display: inline-block;
    }
    
    /* Entregáveis — mini antes/depois */
    .sistema-page .entregavel-item--ad { align-items: flex-start; }
    .sistema-page .entregavel-body { display: flex; flex-direction: column; gap: 5px; }
    .sistema-page .entregavel-titulo { font-family: var(--font-h); font-size: 1rem; font-weight: 700; color: var(--text-light); margin-bottom: 2px; }
    .sistema-page .entregavel-antes { font-size: 0.82rem; color: rgba(240,237,230,0.38); line-height: 1.5; }
    .sistema-page .entregavel-antes::before { content: "Antes: "; font-weight: 600; color: rgba(239,68,68,0.55); }
    .sistema-page .entregavel-depois { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }
    .sistema-page .entregavel-depois::before { content: "Depois: "; font-weight: 600; color: var(--green); }

    /* Demo — bloco de curiosidade */
    .sistema-page .demo-curiosidade { max-width: 600px; margin: 32px auto 0; background: rgba(255,255,255,0.03); border: 1px solid var(--border-primary); border-radius: var(--radius); padding: 28px 32px; }
    .sistema-page .demo-curiosidade-titulo { font-family: var(--font-h); font-size: 1.05rem; font-weight: 700; color: var(--text-light); margin-bottom: 16px; }
    .sistema-page .demo-curiosidade-list { list-style: none; display: flex; flex-direction: column; gap: 12px; }
    .sistema-page .demo-curiosidade-list li { font-size: 0.92rem; color: var(--text-muted); padding-left: 20px; position: relative; line-height: 1.5; }
    .sistema-page .demo-curiosidade-list li::before { content: "→"; position: absolute; left: 0; color: var(--primary); font-weight: 700; }

    .sistema-page .cta-final-filosofia::before {
      content: '"';
      font-size: 5rem;
      color: rgba(232,135,30,0.1);
      position: absolute;
      top: -20px; left: -30px;
      font-family: var(--font-h);
      line-height: 1;
      pointer-events: none;
    }
  
/* ============================================================
   OVERRIDES — Revisão de layout (desk/tablet/mobile)
   ============================================================ */

/* Logo Brand no hero — espaçamento equivalente ao placeholder */
.sistema-page .hero-logo { margin-bottom: 40px; }

/* Foto real do Rodrigo — substitui o placeholder/silhueta */
.sistema-page .autor-foto-real {
  width: 220px;
  height: 220px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  box-shadow: 0 14px 40px rgba(0,0,0,0.4);
}
.sistema-page .autor-foto-real img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
}

/* Prints reais nos devices — substituem o placeholder */
.sistema-page .device-screen--image {
  padding: 0;
  background: #0F1A14;
  overflow: hidden;
}
.sistema-page .device-screen--image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
  display: block;
}
.sistema-page .device-screen-inner--image {
  padding: 0;
  background: #0F1A14;
  overflow: hidden;
  border-radius: 14px;
}
.sistema-page .device-screen-inner--image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
  display: block;
}

/* ── Quebras de texto (<br />) em mobile/tablet ── */
/* Em telas menores, vários títulos e labels têm <br /> que quebram feio.
   Solução: até 768px, ignoramos os <br /> (line-break: auto) e deixamos a tipografia respirar com balance. */
@media (max-width: 768px) {
  .sistema-page h1,
  .sistema-page h2,
  .sistema-page .ad-anchor-quote,
  .sistema-page .antes-depois-headline h2,
  .sistema-page .urgencia-header h2,
  .sistema-page .cta-final h2,
  .sistema-page .urgencia-label,
  .sistema-page .urgencia-detail,
  .sistema-page .step-desc,
  .sistema-page .emblema-label,
  .sistema-page .hero-sub {
    text-wrap: balance;
  }
  .sistema-page h1 br,
  .sistema-page h2 br,
  .sistema-page .ad-anchor-quote br,
  .sistema-page .urgencia-header h2 br,
  .sistema-page .cta-final h2 br {
    display: none;
  }
}

/* Hero — evitar overflow horizontal e garantir leitura */
@media (max-width: 640px) {
  .sistema-page .hero h1 {
    font-size: clamp(2rem, 8vw, 2.6rem);
    padding: 0 4px;
  }
  .sistema-page .hero-sub { padding: 0 8px; }
  .sistema-page .trust-row { gap: 12px 18px; }
  .sistema-page .browser-content { padding: 12px; }
  .sistema-page .dash-table-row { font-size: 0.6rem; }
}

/* Tablet — ajustes finos do hero e cards */
@media (min-width: 641px) and (max-width: 1023px) {
  .sistema-page .hero h1 { font-size: clamp(2.4rem, 5vw, 3.4rem); }
  .sistema-page .grid-4 { grid-template-columns: repeat(2, 1fr); }
  .sistema-page .photo-card { min-height: 240px; }
  .sistema-page .metodo-steps {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .sistema-page .metodo-connector { padding: 12px 0; }
  .sistema-page .metodo-connector-line { width: 40px; height: 2px; }
  .sistema-page .urgencia-calc {
    grid-template-columns: 1fr;
    gap: 8px 0;
  }
  .sistema-page .urgencia-connector { flex-direction: row; gap: 8px; padding: 4px 0; }
  /* devices em fila ficam apertados no tablet */
  .sistema-page .devices-wrap {
    flex-wrap: wrap;
    justify-content: center;
    gap: 28px;
  }
  .sistema-page .device-desktop { max-width: 520px; flex: 1 1 100%; }
  .sistema-page .device-tablet { width: 180px; }
  .sistema-page .device-phone { width: 120px; }
  /* autoridade — stack */
  .sistema-page .autoridade-grid {
    grid-template-columns: 1fr;
    gap: 32px;
    justify-items: center;
    text-align: center;
  }
  .sistema-page .autor-badges { justify-content: center; }
}

/* Comp-table — em mobile, evitar valores espremidos */
@media (max-width: 480px) {
  .sistema-page .comp-table-header,
  .sistema-page .comp-row {
    grid-template-columns: 1fr 48px 48px;
    gap: 8px;
    padding: 12px 14px;
  }
  .sistema-page .comp-row-label { font-size: 0.88rem; }
  .sistema-page .comp-row-label strong { font-size: 0.95rem; }
  .sistema-page .comp-cell { font-size: 1rem; }
}

/* Antes/depois — não cortar bordas no mobile */
@media (max-width: 767px) {
  .sistema-page .ad-grid { gap: 12px; }
}

/* Autoridade emblema — alinhar largura com a foto */
.sistema-page .autoridade-emblema { max-width: 220px; }

/* Bonus card — evitar overflow do badge em telas estreitas */
@media (max-width: 480px) {
  .sistema-page .bonus-badge {
    font-size: 0.65rem;
    padding: 5px 14px;
    white-space: nowrap;
    max-width: 90%;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .sistema-page .bonus-card { padding: 36px 20px 28px; }
}

/* Offer-box — paddings menores no mobile */
@media (max-width: 480px) {
  .sistema-page .offer-box { padding: 28px 18px; }
  .sistema-page .entregavel-item { font-size: 0.9rem; }
}

/* Dash preview no hero — empilhar tabela em mobile estreito */
@media (max-width: 380px) {
  .sistema-page .dash-table-row {
    grid-template-columns: 1.4fr 1fr 1fr;
  }
  .sistema-page .dash-table-row > div:nth-child(3) { display: none; }
}

/* ============================================================
   Ajustes finos mobile — correções pós-revisão
   ============================================================ */

/* "Funciona para qualquer..." — em mobile, 1 coluna evita texto explodindo */
@media (max-width: 640px) {
  .sistema-page .grid-4 {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .sistema-page .photo-card {
    min-height: 260px;
    padding: 22px;
  }
  .sistema-page .photo-card-content h3 {
    font-size: 1.15rem;
    line-height: 1.3;
  }
  .sistema-page .photo-card-question {
    font-size: 0.92rem;
  }
}

/* Em tablet pequeno (≤ 820px), 2 colunas com mais respiro */
@media (min-width: 641px) and (max-width: 820px) {
  .sistema-page .grid-4 { grid-template-columns: repeat(2, 1fr); gap: 18px; }
  .sistema-page .photo-card { min-height: 280px; padding: 24px; }
  .sistema-page .photo-card-content h3 { font-size: 1.25rem; line-height: 1.3; }
}

/* Device phone — imagem do print deve ocupar toda a tela, sem moldura interna */
.sistema-page .device-phone .device-screen-inner--image {
  aspect-ratio: 9 / 19.5;
  padding: 0;
  background: #000;
  border-radius: 14px;
  overflow: hidden;
  width: 100%;
}
.sistema-page .device-phone .device-screen-inner--image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
}
/* Em mobile, aumentar o phone para usar melhor a largura disponível */
@media (max-width: 640px) {
  .sistema-page .device-phone { width: 200px; }
  .sistema-page .device-tablet { width: 220px; }
}

/* "O software custa vs Sem controle" — desktop: melhor respiro, evitar texto colado */
.sistema-page .urgencia-resolve {
  flex-wrap: nowrap;
}
.sistema-page .urgencia-resolve-col {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.sistema-page .urgencia-resolve-price,
.sistema-page .urgencia-resolve-loss {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  white-space: nowrap;
}

/* ============================================================
   Correções tabela comparação + urgência mobile/tablet
   ============================================================ */

/* Header da tabela comparação — colunas mais largas e wrap permitido */
.sistema-page .comp-table-header {
  grid-template-columns: 1fr 110px 110px;
  align-items: end;
}
.sistema-page .comp-table-header span {
  line-height: 1.25;
  word-break: keep-all;
  hyphens: none;
}
.sistema-page .comp-row {
  grid-template-columns: 1fr 110px 110px;
}

/* Tablet — manter colunas confortáveis */
@media (max-width: 1023px) {
  .sistema-page .comp-table-header,
  .sistema-page .comp-row {
    grid-template-columns: 1fr 90px 90px;
    gap: 10px;
    padding: 14px 18px;
  }
  .sistema-page .comp-table-header span { font-size: 0.68rem; letter-spacing: 0.08em; }
}

/* Mobile bem estreito — reduz mais e quebra label se preciso */
@media (max-width: 480px) {
  .sistema-page .comp-table-header,
  .sistema-page .comp-row {
    grid-template-columns: 1fr 56px 56px;
    gap: 6px;
    padding: 12px 12px;
  }
  .sistema-page .comp-table-header span { font-size: 0.62rem; }
}

/* Urgência resolve — em tablet/mobile (column), respira sem encostar nas bordas */
@media (max-width: 768px) {
  .sistema-page .urgencia-resolve {
    border: none;
    background: transparent;
    gap: 12px;
    overflow: visible;
  }
  .sistema-page .urgencia-resolve-col {
    border-radius: var(--radius);
    border: 1px solid var(--border-subtle);
    width: 100%;
    min-height: auto;
    padding: 26px 22px;
  }
}

    /* Floating orbs */
    .sistema-page .sp-orb {
      position: absolute; border-radius: 50%;
      filter: blur(90px); pointer-events: none; mix-blend-mode: screen;
    }
    .sistema-page .sp-orb-1 {
      width: 600px; height: 600px; background: hsl(36,55%,62%);
      top: -200px; right: -100px; opacity: 0.10;
      animation: spOrbPulse 8s ease-in-out infinite;
    }
    .sistema-page .sp-orb-2 {
      width: 400px; height: 400px; background: hsl(165,60%,40%);
      bottom: -80px; left: -80px; opacity: 0.07;
      animation: spOrbPulse 8s ease-in-out infinite; animation-delay: -4s;
    }
    @keyframes spOrbPulse {
      0%,100% { transform: scale(1) translate(0,0); }
      50%      { transform: scale(1.2) translate(16px,-16px); }
    }
    @media(max-width:767px){
      .sistema-page .sp-orb-1 { width: 280px; height: 280px; top: -100px; right: -60px; }
      .sistema-page .sp-orb-2 { width: 200px; height: 200px; }
    }
    @media (prefers-reduced-motion: reduce) {
      .sistema-page .sp-orb { animation: none; }
    }

    /* Eyebrow com linhas laterais */
    .sistema-page .eyebrow-lined {
      display: inline-flex; align-items: center; gap: 12px;
    }
    .sistema-page .eyebrow-lined::before,
    .sistema-page .eyebrow-lined::after {
      content: ''; flex-shrink: 0; width: 32px; height: 1px;
      background: var(--border-primary);
    }

    /* Divisor gold entre seções */
    .sistema-page .sp-divider {
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--border-primary), transparent);
    }
    .sp-wave { display:block; width:100%; overflow:hidden; line-height:0; }

    /* Anel giratório — foto Rodrigo */
    .sistema-page .autor-foto-ring-wrap {
      position: relative; width: 220px; height: 220px; flex-shrink: 0;
    }
    .sistema-page .autor-ring {
      position: absolute; inset: -10px; border-radius: 50%;
      border: 2px solid transparent;
      border-top-color: var(--primary);
      border-right-color: var(--border-primary);
      animation: spRingRotate 7s linear infinite;
      pointer-events: none;
    }
    .sistema-page .autor-ring-2 {
      position: absolute; inset: -5px; border-radius: 50%;
      border: 1px solid transparent;
      border-bottom-color: hsla(36,55%,62%,0.22);
      animation: spRingRotate 12s linear infinite reverse;
      pointer-events: none;
    }
    @keyframes spRingRotate { to { transform: rotate(360deg); } }
    @media (prefers-reduced-motion: reduce) {
      .sistema-page .autor-ring, .sistema-page .autor-ring-2 { animation: none; }
    }

    /* Sticky CTA bar — mobile only */
    .sp-sticky {
      position: fixed; inset: auto 0 0 0; z-index: 100;
      background: hsla(165,50%,8%,0.96);
      border-top: 1px solid var(--border-primary);
      padding: 12px 16px 16px;
      backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      transform: translateY(100%);
      transition: transform 0.4s cubic-bezier(0.22,1,0.36,1);
    }
    .sp-sticky.sp-sticky--visible { transform: translateY(0); }
    .sp-sticky-btn {
      display: flex; align-items: center; justify-content: center;
      width: 100%; height: 50px; border-radius: 8px;
      background: var(--grad-gold); color: hsl(165,60%,8%);
      font-family: var(--font-b); font-weight: 700; font-size: 0.95rem;
      text-decoration: none; position: relative; overflow: hidden;
    }
    .sp-sticky-btn::after {
      content: ''; position: absolute; inset: 0;
      background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.35) 50%, transparent 70%);
      transform: translateX(-100%);
      animation: spShimmerSticky 3s ease-in-out infinite;
    }
    @keyframes spShimmerSticky {
      0%,40% { transform: translateX(-100%); }
      70%,100% { transform: translateX(100%); }
    }
    .sp-sticky-trust {
      text-align: center; font-size: 0.65rem; color: var(--text-muted); margin-top: 6px;
    }
    @media(min-width: 768px) { .sp-sticky { display: none !important; } }
`}</style>
    <div className="sistema-page">



  {/* ==========================================
       DOBRA 1 — HERO
  ========================================== */}
  <section className="hero">
    {/* Floating orbs */}
    <div className="sp-orb sp-orb-1"></div>
    <div className="sp-orb sp-orb-2"></div>

    <div className="container">
      <div className="hero-inner">

        {/* Coluna esquerda — texto */}
        <div className="hero-left">
          <h1>
            Você vende bem —
            <em>e ainda assim o dinheiro some.</em>
          </h1>

          <p className="hero-sub">
            Descubra, em 5 minutos, quanto cada prato realmente lucra — e pare de perder margem sem perceber.
          </p>

          {/* Big Idea Visual — 14% */}
          <div className="hero-stat-anchor">
            <span className="hero-stat-num">
              14<span className="hero-stat-pct">%</span>
            </span>
            <span className="hero-stat-label">de margem — o que donos alcançam com o método</span>
            <span className="hero-stat-divider"></span>
          </div>

          <div className="hero-cta-wrap">
            <a href="https://pay.hotmart.com/G104668166T" className="btn btn-primary">
              Quero ver quanto cada prato realmente lucra →
            </a>
            <div className="trust-row">
              <span className="trust-item">R$ 97/mês</span>
              <span className="trust-item">Acesso imediato</span>
              <span className="trust-item">Cancele quando quiser</span>
            </div>
          </div>
        </div>

        {/* Coluna direita — dashboard mockup */}
        <div className="hero-right">
        <div className="mockup-wrap">
          <div className="browser-frame">
            <div className="browser-bar">
              <div className="browser-dot"></div><div className="browser-dot"></div><div className="browser-dot"></div>
              <div className="browser-url">Software Dono 14% — Painel de Gestão</div>
            </div>
            <div className="browser-content" style={{padding:0,overflow:"hidden"}}>
              <img
                src={sistemaHeroImg}
                alt="Software Dono 14% — interface"
                style={{width:"100%",display:"block"}}
                loading="lazy"
                decoding="async"
              />
            </div>
          </div>
        </div>

        </div>{/* hero-right */}

      </div>{/* hero-inner */}
    </div>{/* container */}
  </section>

<div className="sp-wave" aria-hidden="true">
    <svg viewBox="0 0 1200 28" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style={{width:"100%",height:28,display:"block"}}>
      <path d="M0,14 Q150,4 300,14 Q450,24 600,14 Q750,4 900,14 Q1050,24 1200,14" fill="none" stroke="var(--border-primary)" strokeWidth="1" strokeOpacity="0.4" />
    </svg>
  </div>

  {/* ==========================================
       DOBRA 2 — DEMO / VÍDEO
  ========================================== */}
  <section className="section-dark glow-top">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>Veja funcionando</span>
        <h2>Em 5 minutos você sabe quanto<br />cada prato realmente lucra</h2>
        <p>O Rodrigo mostra ao vivo como funciona — e como você configura o seu em menos de uma tarde.</p>
      </div>

      <div className="video-frame">
        <div className="play-btn"><div className="play-icon"></div></div>
        <div className="video-label">Demonstração completa do Software Dono 14% · ~7 minutos</div>
      </div>

      <div className="demo-curiosidade anim-fade-up">
        <p className="demo-curiosidade-titulo">Veja o sistema funcionando em um restaurante real</p>
        <ul className="demo-curiosidade-list">
          <li>Como cadastrar seu primeiro prato em menos de 5 minutos.</li>
          <li>Como descobrir, ao vivo, qual prato está sabotando seu lucro.</li>
          <li>Como usar o simulador para aumentar preço sem perder cliente.</li>
        </ul>
      </div>
    </div>
  </section>


  {/* ==========================================
       DOBRA 3 — PARA QUEM É
       (cards com fundo de foto)
  ========================================== */}
  <section className="section-dark glow-side">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>É para você?</span>
        <h2>Funciona para qualquer<br />tipo de restaurante</h2>
        <p>Delivery, físico, lanchonete ou pizzaria — o cálculo é baseado em margem real, não no tipo de cozinha.</p>
      </div>

      <div className="grid-4" style={{marginTop: "56px"}}>

        <div className="photo-card">
          <div className="photo-card-bg photo-card-bg--burguer"></div>
          <div className="photo-card-overlay"></div>
          <span className="photo-card-tag">Hamburgueria · Delivery</span>
          <div className="photo-card-content">
            <p className="photo-card-question">Você sabe que o combo de R$35 lucra — mas e o de R$28?</p>
            <h3>Custo real por combo, margem por produto, controle de perdas.</h3>
          </div>
        </div>

        <div className="photo-card">
          <div className="photo-card-bg photo-card-bg--pizza"></div>
          <div className="photo-card-overlay"></div>
          <span className="photo-card-tag">Pizzaria</span>
          <div className="photo-card-content">
            <p className="photo-card-question">Cada sabor tem custo diferente. Você cobra igual para todos?</p>
            <h3>Precifique cada pizza pelo custo real. Saiba qual sabor compra lucro — e qual consome.</h3>
          </div>
        </div>

        <div className="photo-card">
          <div className="photo-card-bg photo-card-bg--rest"></div>
          <div className="photo-card-overlay"></div>
          <span className="photo-card-tag">Restaurante · À la carte</span>
          <div className="photo-card-content">
            <p className="photo-card-question">Cardápio com 20 pratos. Quantos realmente sobram no caixa?</p>
            <h3>Margem definida por prato. Sem achismo. Sem susto no fim do mês.</h3>
          </div>
        </div>

        <div className="photo-card">
          <div className="photo-card-bg photo-card-bg--cafe"></div>
          <div className="photo-card-overlay"></div>
          <span className="photo-card-tag">Lanchonete · Café</span>
          <div className="photo-card-content">
            <p className="photo-card-question">Do coxinha ao café especial — qual deles deixa mais no caixa?</p>
            <h3>Custo, margem e preço de cada item. Na palma da mão. Sem planilha.</h3>
          </div>
        </div>

      </div>

      {/* Qualificação negativa */}
      <div className="para-quem-nao">
        <div className="para-quem-sim">
          <div className="para-quem-nao-label">É para você se…</div>
          <div className="pq-item"><span className="pq-item-icon-sim">✓</span><span>Você vende mas não vê o lucro aparecer no fim do mês</span></div>
          <div className="pq-item"><span className="pq-item-icon-sim">✓</span><span>Você precifica no chute ou copiando o concorrente</span></div>
          <div className="pq-item"><span className="pq-item-icon-sim">✓</span><span>Você quer decidir com número, não com instinto</span></div>
          <div className="pq-item"><span className="pq-item-icon-sim">✓</span><span>Você trabalha no delivery, físico ou em qualquer combinação</span></div>
        </div>
        <div className="para-quem-nao-col">
          <div className="para-quem-nao-label">Não é para você se…</div>
          <div className="pq-item"><span className="pq-item-icon-nao">✗</span><span>Você já tem contador ativo fazendo controle de margem por prato</span></div>
          <div className="pq-item"><span className="pq-item-icon-nao">✗</span><span>Você já usa um sistema de BI com CMV automatizado</span></div>
          <div className="pq-item"><span className="pq-item-icon-nao">✗</span><span>Você não quer mudar nada — só está buscando desculpa para o caixa ruim</span></div>
        </div>
      </div>

    </div>
  </section>


  {/* ==========================================
       DOBRA 4 — DISPOSITIVOS
       (prints mobile + tablet + desktop)
  ========================================== */}
  <section className="devices-section glow-top">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>Em qualquer tela</span>
        <h2>Acesse onde e quando precisar</h2>
        <p>No computador antes de fechar o mês. No celular na hora de comprar do fornecedor. No tablet durante o expediente.</p>
      </div>

      <div className="devices-wrap">

        {/* Desktop */}
        <div className="device-desktop">
          <div className="device-frame">
            <div className="device-bar">
              <div className="device-dot" style={{background: "#FF5F57"}}></div>
              <div className="device-dot" style={{background: "#FEBC2E"}}></div>
              <div className="device-dot" style={{background: "#28C840"}}></div>
            </div>
            <div className="device-screen device-screen--image">
              <img
                src={sistemaPrintDesktop}
                alt="Tela de Produtos do sistema — visão desktop"
                loading="lazy"
                decoding="async"
              />
            </div>
          </div>
          <div className="device-stand"></div>
          <div className="device-base"></div>
        </div>

        {/* Tablet */}
        <div className="device-tablet">
          <div className="device-frame">
            <div className="device-screen-inner device-screen-inner--image">
              <img
                src={sistemaTabletImg}
                alt="Software Dono 14% — visão tablet"
                style={{width:"100%",height:"100%",objectFit:"cover",display:"block"}}
                loading="lazy"
                decoding="async"
              />
            </div>
          </div>
        </div>

        {/* Phone */}
        <div className="device-phone">
          <div className="device-frame">
            <div className="device-notch"></div>
            <div className="device-screen-inner device-screen-inner--image">
              <img
                src={sistemaPrintMobile}
                alt="Tela de Produtos do sistema — visão mobile"
                loading="lazy"
                decoding="async"
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  </section>



  {/* ==========================================
       DOBRA MÉTODO DCAL — Como funciona
  ========================================== */}
  <section className="metodo-section">
    <div className="container">

      <div className="metodo-title-block">
        <span className="eyebrow" style={{display: "inline-flex", marginBottom: "24px"}}><span className="eyebrow-dot"></span>Como funciona</span>
        <div className="metodo-name">Método <span>DCAL</span></div>
        <div className="metodo-tagline" style={{marginTop: "14px"}}>
          <span className="tl-word">Custo</span>
          <span className="tl-arrow">→</span>
          <span className="tl-word">Preço</span>
          <span className="tl-arrow">→</span>
          <span className="tl-word">Margem</span>
        </div>
        <p style={{marginTop: "20px", color: "var(--text-muted)", fontSize: "0.95rem", maxWidth: "480px", marginLeft: "auto", marginRight: "auto"}}>Cada passo depende do anterior. É assim que gestão real funciona.</p>
      </div>

      <div className="metodo-steps">

        <div className="metodo-step anim-fade-up anim-delay-1">
          <div className="step-num">01</div>
          <div className="step-badge">01</div>
          <div className="step-title">Custo Real</div>
          <p className="step-desc">Cadastre ingredientes, embalagens e despesas. O sistema calcula automaticamente o custo real de cada prato — com perdas incluídas. Sem estimativa.</p>
          <span className="step-result">Você sabe o que custa</span>
        </div>

        <div className="metodo-connector">
          <div className="metodo-connector-inner">
            <div className="metodo-connector-line"></div>
            <div className="metodo-connector-arrow">▼</div>
          </div>
        </div>

        <div className="metodo-step anim-fade-up anim-delay-2">
          <div className="step-num">02</div>
          <div className="step-badge">02</div>
          <div className="step-title">Preço Defendido</div>
          <p className="step-desc">Defina sua margem alvo. O sistema calcula o preço ideal na hora. Você ajusta com segurança — porque o número está do seu lado, não o concorrente.</p>
          <span className="step-result">Você sabe o que cobrar</span>
        </div>

        <div className="metodo-connector">
          <div className="metodo-connector-inner">
            <div className="metodo-connector-line"></div>
            <div className="metodo-connector-arrow">▼</div>
          </div>
        </div>

        <div className="metodo-step anim-fade-up anim-delay-3">
          <div className="step-num">03</div>
          <div className="step-badge">03</div>
          <div className="step-title">Margem Controlada</div>
          <p className="step-desc">Monitore CMV em tempo real. Veja quais pratos sabotam seu lucro. Simule cenários antes de decidir. Aja antes do problema aparecer.</p>
          <span className="step-result">Você sabe o que sobra</span>
        </div>

      </div>

      <div className="metodo-footer">
        <p>"Lucro não é sorte. É <em>decisão baseada em número.</em>"</p>
      </div>

    </div>
  </section>

  {/* ==========================================
       DOBRA 5 — FUNCIONALIDADES
  ========================================== */}
  <section className="section-dark glow-top">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>O que você tem acesso</span>
        <h2>Tudo que você precisa para<br />trabalhar com lucro real</h2>
        <p>Focado no que importa: custo, margem e decisão. Sem abas inúteis, sem curva de aprendizado longa.</p>
      </div>

      <div className="feat-grid">
        <div className="feat-card feat-card--dark">
          <div className="feat-num">01</div>
          <h3>Ficha Técnica Inteligente</h3>
          <p>Cadastre ingredientes, defina quantidades e o sistema calcula automaticamente o custo real de cada prato — incluindo perdas e variações.</p>
          <span className="tag">Custo real</span>
        </div>
        <div className="feat-card feat-card--dark">
          <div className="feat-num">02</div>
          <h3>Precificação por Margem</h3>
          <p>Defina a margem que você quer e receba o preço calculado na hora. Sem chute. Sem medo. Com número.</p>
          <span className="tag">Preço correto</span>
        </div>
        <div className="feat-card feat-card--dark">
          <div className="feat-num">03</div>
          <h3>Monitor de CMV</h3>
          <p>Acompanhe seu Custo de Mercadoria Vendida em tempo real. Saiba imediatamente quando algo sai do controle.</p>
          <span className="tag">Controle em tempo real</span>
        </div>
        <div className="feat-card feat-card--dark">
          <div className="feat-num">04</div>
          <h3>Relatório de Rentabilidade</h3>
          <p>Veja quais pratos são campeões e quais são vilões do lucro. Decida com dados, não com feeling.</p>
          <span className="tag">Decisão inteligente</span>
        </div>
        <div className="feat-card feat-card--dark">
          <div className="feat-num">05</div>
          <h3>Simulador de Cenários</h3>
          <p>Antes de mudar preço ou cardápio, simule o impacto. A segurança de decidir com projeção real.</p>
          <span className="tag">Segurança para decidir</span>
        </div>
        {/* Feature destacado: tutoriais no sistema */}
        <div className="feat-card feat-card--dark feat-card--highlight">
          <div className="feat-num">▶</div>
          <h3>Tutorial de Vídeo em Cada Menu</h3>
          <p>Toda funcionalidade do sistema tem um vídeo de tutorial integrado. A dúvida aparece? O vídeo está ali. Você aprende na hora certa, sem precisar sair do sistema.</p>
          <span className="tag">Suporte contextual</span>
        </div>
      </div>

    </div>
  </section>


  {/* ==========================================
       DOBRA 6 — BÔNUS
  ========================================== */}
  <section className="section-alt glow-top" style={{borderTop: "1px solid var(--border-primary)"}}>
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>Incluído no acesso</span>
        <h2>Você não começa sozinho</h2>
        <p>Junto com o software, você recebe o que precisa para configurar tudo do zero e enxergar resultados rápido.</p>
      </div>

      <div className="bonus-card">
        <div className="bonus-badge">Bônus — Incluído no acesso</div>
        <h3>Tutorial Completo:<br />do Zero ao Primeiro Preço Formado</h3>
        <p>Passo a passo em vídeo para cadastrar seu primeiro prato, montar sua ficha técnica e formar o preço com margem real — mesmo que você nunca tenha usado um software de gestão antes.</p>
        <p style={{marginTop: "20px", fontSize: "0.9rem", color: "var(--text-muted)"}}>+ Suporte direto via <strong style={{color: "var(--primary)"}}>WhatsApp</strong> para tirar dúvidas enquanto você configura.</p>
      </div>
    </div>
  </section>


  {/* ==========================================
       DOBRA 7 — DEPOIMENTOS
       (placeholder — sem números falsos)
  ========================================== */}
  <section className="section-ultra glow-side">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>O que dizem os donos</span>
        <h2>Quem parou de torcer<br />e começou a controlar</h2>
        <p>Em breve — resultados reais de donos que usam o método.</p>
      </div>

      <div className="depo-grid">
        <div className="depo-card depo-card--placeholder anim-fade-up anim-delay-1">
          <div className="depo-placeholder-header"></div>
          <div className="depo-placeholder-body">
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-avatar">
              <div className="depo-placeholder-circle"></div>
              <div className="depo-placeholder-name"></div>
            </div>
          </div>
        </div>
        <div className="depo-card depo-card--placeholder anim-fade-up anim-delay-2">
          <div className="depo-placeholder-header"></div>
          <div className="depo-placeholder-body">
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-avatar">
              <div className="depo-placeholder-circle"></div>
              <div className="depo-placeholder-name"></div>
            </div>
          </div>
        </div>
        <div className="depo-card depo-card--placeholder anim-fade-up anim-delay-3">
          <div className="depo-placeholder-header"></div>
          <div className="depo-placeholder-body">
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-line"></div>
            <div className="depo-placeholder-avatar">
              <div className="depo-placeholder-circle"></div>
              <div className="depo-placeholder-name"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

<div className="sp-wave" aria-hidden="true">
    <svg viewBox="0 0 1200 28" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style={{width:"100%",height:28,display:"block"}}>
      <path d="M0,14 Q150,4 300,14 Q450,24 600,14 Q750,4 900,14 Q1050,24 1200,14" fill="none" stroke="var(--border-primary)" strokeWidth="1" strokeOpacity="0.4" />
    </svg>
  </div>

  {/* ==========================================
       DOBRA 8 — ANTES / DEPOIS
       (dramático, vivo, emocional)
  ========================================== */}
  <section className="antes-depois-section">
    <div className="container antes-depois-inner">

      <div className="antes-depois-headline">
        <h2>
          Imagine fechar o mês...<br />
          <em>e realmente ver dinheiro sobrar.</em>
        </h2>
        <p>Não é magia. É controle. A diferença começa quando você para de trabalhar no escuro.</p>
      </div>

      <div className="ad-grid">
        <div className="ad-col ad-col--antes">
          <div className="ad-col-label">✗ &nbsp; Como é hoje</div>

          <div className="ad-item">
            <div className="ad-icon">✗</div>
            <div className="ad-item-text">
              <strong>Caixa no vermelho sem saber por quê</strong>
              <span>O dinheiro foi embora e você só descobre depois.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✗</div>
            <div className="ad-item-text">
              <strong>Fim de mês no susto</strong>
              <span>Você torce para fechar as contas. É assim todo mês.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✗</div>
            <div className="ad-item-text">
              <strong>Preço no chute</strong>
              <span>Você olha o concorrente e reza para não perder cliente.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✗</div>
            <div className="ad-item-text">
              <strong>Trabalha muito, sobra pouco</strong>
              <span>O restaurante cresce mas o lucro não acompanha.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✗</div>
            <div className="ad-item-text">
              <strong>Depende do fim de semana para salvar o mês</strong>
              <span>Um dia ruim e tudo desmorona.</span>
            </div>
          </div>
        </div>

        <div className="ad-col ad-col--depois">
          <div className="ad-col-label">✓ &nbsp; Como pode ser</div>

          <div className="ad-item">
            <div className="ad-icon">✓</div>
            <div className="ad-item-text">
              <strong>Sabe o que vai sobrar antes de fechar</strong>
              <span>Você acompanha o CMV em tempo real e age antes do problema.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✓</div>
            <div className="ad-item-text">
              <strong>Fim de mês previsível</strong>
              <span>Sem surpresa. Você sabe exatamente o que vai acontecer.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✓</div>
            <div className="ad-item-text">
              <strong>Preço formado por número</strong>
              <span>Você ajusta com segurança — sem medo de perder cliente.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✓</div>
            <div className="ad-item-text">
              <strong>Cada prato tem margem definida</strong>
              <span>Você trabalha com propósito. O cardápio trabalha por você.</span>
            </div>
          </div>
          <div className="ad-item">
            <div className="ad-icon">✓</div>
            <div className="ad-item-text">
              <strong>Lucro é rotina, não sorte</strong>
              <span>Você não torce mais. Você controla.</span>
            </div>
          </div>
        </div>
      </div>

      <div className="ad-anchor">
        <p className="ad-anchor-quote">"Isso é ser um <em>Dono 14%.</em>"</p>
        <p className="ad-anchor-sub">Não é sorte. É método.</p>
      </div>

    </div>
  </section>

  <div className="sp-wave" aria-hidden="true">
    <svg viewBox="0 0 1200 28" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style={{width:"100%",height:28,display:"block"}}>
      <path d="M0,14 Q150,4 300,14 Q450,24 600,14 Q750,4 900,14 Q1050,24 1200,14" fill="none" stroke="var(--border-primary)" strokeWidth="1" strokeOpacity="0.4" />
    </svg>
  </div>

  {/* ==========================================
       DECORADO — Vida do outro lado
  ========================================== */}
  <section className="decorado-section">
    <div className="container">
      <div className="decorado-inner">

        <div className="decorado-eyebrow"><span className="eyebrow eyebrow-lined">A vida do outro lado</span></div>

        <div className="decorado-lines">
          <p className="decorado-line">
            Você fecha o mês <em>sabendo o número antes de o mês acabar.</em>
          </p>
          <p className="decorado-line">
            Você vai ao fornecedor com <em>clareza de quanto pode pagar</em> — sem travar na negociação.
          </p>
          <p className="decorado-line">
            Você ajusta preço <em>sem medo de perder cliente</em> — porque o número está do seu lado.
          </p>
          <p className="decorado-line">
            Você para de torcer para o fim de semana salvar o mês. <em>O mês já estava salvo.</em>
          </p>
        </div>

        <div className="decorado-mantra">Isso não é sorte. É controle.</div>

      </div>
    </div>
  </section>

  <div className="sp-wave" aria-hidden="true">
    <svg viewBox="0 0 1200 28" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style={{width:"100%",height:28,display:"block"}}>
      <path d="M0,14 Q150,4 300,14 Q450,24 600,14 Q750,4 900,14 Q1050,24 1200,14" fill="none" stroke="var(--border-primary)" strokeWidth="1" strokeOpacity="0.4" />
    </svg>
  </div>

  {/* ==========================================
       URGÊNCIA — O custo de não saber
  ========================================== */}
  <section className="urgencia-section">
    <div className="container">

      <div className="urgencia-header">
        <span className="eyebrow" style={{display: "inline-flex", marginBottom: "24px"}}><span className="eyebrow-dot"></span>O custo de não saber</span>
        <h2>Quanto você está perdendo<br /><em>agora, sem perceber?</em></h2>
        <p>Não é projeção. É matemática. Um único prato com custo errado já conta.</p>
      </div>

      <div className="urgencia-calc">

        <div className="urgencia-card urgencia-card--1 anim-fade-up anim-delay-1">
          <div className="urgencia-tag">Por prato</div>
          <div className="urgencia-num" data-target="2">R$ 2</div>
          <div className="urgencia-label">a mais no custo real<br />do que você imagina</div>
          <div className="urgencia-detail">
            Um ingrediente com preço errado.<br />
            Uma perda não contabilizada.<br />
            Margem calculada no chute.
          </div>
        </div>

        <div className="urgencia-connector">×150<br /><span>pratos/mês</span></div>

        <div className="urgencia-card urgencia-card--2 anim-fade-up anim-delay-2">
          <div className="urgencia-tag">Por mês</div>
          <div className="urgencia-num" data-target="300">R$ 300</div>
          <div className="urgencia-label">de margem perdida<br />todo mês</div>
          <div className="urgencia-detail">
            150 pratos × R$2 de erro.<br />
            Mês após mês. Sem perceber.<br />
            Sem como recuperar.
          </div>
        </div>

        <div className="urgencia-connector">×12<br /><span>meses/ano</span></div>

        <div className="urgencia-card urgencia-card--3 anim-fade-up anim-delay-3">
          <div className="urgencia-tag">Por ano</div>
          <div className="urgencia-num" data-target="3600">R$ 3.600</div>
          <div className="urgencia-label">de margem que você achou<br />que tinha. <strong style={{color: "#FF5040"}}>Mas não tinha.</strong></div>
          <div className="urgencia-detail">
            Quase R$4.000 que poderiam<br />
            estar no seu caixa.<br />
            Foram para o custo sem aviso.
          </div>
        </div>

      </div>

      {/* Resolução: R$97 vs R$300+ */}
      <div className="urgencia-resolve anim-fade-up anim-delay-4">
        <div className="urgencia-resolve-col urgencia-resolve-col--win">
          <span className="urgencia-resolve-label">O software custa</span>
          <div className="urgencia-resolve-price">R$ 97 <span>/mês</span></div>
          <div className="urgencia-resolve-sublabel">Para parar de perder margem</div>
        </div>
        <div className="urgencia-vs">vs</div>
        <div className="urgencia-resolve-col urgencia-resolve-col--lose">
          <span className="urgencia-resolve-label">Sem controle, você perde</span>
          <div className="urgencia-resolve-loss">R$ 300<span>+/mês</span></div>
          <div className="urgencia-resolve-sublabel">Só com 1 prato mal precificado</div>
        </div>
      </div>

      <div className="urgencia-cta-wrap">
        <a href="https://pay.hotmart.com/G104668166T" className="btn btn-primary">
          Parar de perder agora →
        </a>
        <p className="urgencia-footnote">*Baseado em R$2 de erro de margem em 1 prato vendido 5× ao dia. Restaurantes com múltiplos pratos mal precificados perdem proporcionalmente mais.</p>
      </div>

    </div>
  </section>

  {/* ==========================================
       DOBRA 9 — OFERTA + GARANTIA
  ========================================== */}
  <section className="section-dark glow-top">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow eyebrow-lined">Acesso completo</span>
        <h2>Software Oficial do Dono 14%</h2>
        <p>Tudo que você precisa para precificar com precisão, monitorar margem e tomar decisões com dados — em um só lugar.</p>
      </div>

      <div style={{background: "rgba(232,135,30,0.08)", border: "1px solid rgba(232,135,30,0.25)", borderRadius: "12px", padding: "28px 32px", marginBottom: "32px", textAlign: "center"}}>
        <p style={{fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.12em", color: "var(--primary)", fontWeight: "700", marginBottom: "12px"}}>Dado do setor</p>
        <p style={{fontSize: "1.15rem", fontWeight: "600", color: "var(--text-light)", lineHeight: "1.6", margin: "0"}}>Restaurantes que monitoram CMV ativamente operam com margem <strong style={{color: "var(--primary)"}}>5 a 8 pontos percentuais acima</strong> dos que não controlam — na mesma categoria, com o mesmo volume de vendas.</p>
      </div>
      <div className="offer-box" style={{marginTop: "48px"}}>
        <p style={{fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "20px"}}>O que está incluído:</p>
        <div className="entregavel-list">

          <div className="entregavel-item entregavel-item--ad">
            <span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>
            <div className="entregavel-body">
              <strong className="entregavel-titulo">Ficha Técnica Inteligente</strong>
              <span className="entregavel-antes">você estima o custo no chute e não sabe se está lucrando de verdade.</span>
              <span className="entregavel-depois">o sistema calcula o custo real de cada prato — com ingredientes, embalagens e perdas incluídas.</span>
            </div>
          </div>

          <div className="entregavel-item entregavel-item--ad">
            <span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>
            <div className="entregavel-body">
              <strong className="entregavel-titulo">Precificação por Margem</strong>
              <span className="entregavel-antes">você olha o concorrente, arredonda e torce para sobrar algo.</span>
              <span className="entregavel-depois">define a margem que quer e recebe o preço ideal na hora. Com número, sem chute.</span>
            </div>
          </div>

          <div className="entregavel-item entregavel-item--ad">
            <span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>
            <div className="entregavel-body">
              <strong className="entregavel-titulo">Monitor de CMV em Tempo Real</strong>
              <span className="entregavel-antes">você só descobre que a margem foi pro saco quando o mês acaba.</span>
              <span className="entregavel-depois">o sistema te avisa quando o CMV sai da meta — você ajusta antes do prejuízo aparecer.</span>
            </div>
          </div>

          <div className="entregavel-item entregavel-item--ad">
            <span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>
            <div className="entregavel-body">
              <strong className="entregavel-titulo">Relatório de Rentabilidade</strong>
              <span className="entregavel-antes">você tem um feeling de quais pratos vendem, mas não sabe quais realmente sobram.</span>
              <span className="entregavel-depois">vê exatamente quais pratos são campeões e quais estão comendo o seu lucro.</span>
            </div>
          </div>

          <div className="entregavel-item entregavel-item--ad">
            <span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>
            <div className="entregavel-body">
              <strong className="entregavel-titulo">Simulador de Cenários</strong>
              <span className="entregavel-antes">aumentar preço dá medo. E se perder cliente? Você evita e continua com margem ruim.</span>
              <span className="entregavel-depois">simula o impacto antes de decidir. Age com segurança — não com instinto.</span>
            </div>
          </div>

          <div className="entregavel-item"><span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>Atualização dinâmica quando custos mudam</div>
          <div className="entregavel-item"><span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>Tutorial de vídeo em cada menu do sistema</div>
          <div className="entregavel-item"><span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>Tutorial completo: do zero ao primeiro prato precificado</div>
          <div className="entregavel-item"><span className="ent-icon-circle"><Check size={12} color="hsl(165,60%,8%)" strokeWidth={3} /></span>Suporte via WhatsApp</div>
        </div>

        <div className="price-display">
          <div className="price-per">por apenas</div>
          <div className="price-main">R$ 97</div>
          <div className="price-period">por mês</div>
          <div className="price-day">menos de R$ 4 por dia — o custo de parar de trabalhar no escuro</div>
        </div>

        <div style={{textAlign: "center", marginTop: "8px"}}>
          <a href="https://pay.hotmart.com/G104668166T" className="btn btn-primary">
            Começar meu acesso agora →
          </a>
          <div className="trust-row" style={{justifyContent: "center"}}>
            <span className="trust-item">Acesso imediato</span>
            <span className="trust-item">Cancele quando quiser</span>
            <span className="trust-item">Suporte via WhatsApp</span>
          </div>
        </div>

        <div className="garantia-box">
          <div className="garantia-icon"><Lock size={18} color="var(--primary)" /></div>
          <div>
            <h4>Sem contrato. Sem multa. Sem burocracia.</h4>
            <p>Você acessa tudo no ato da compra. Se em algum momento decidir cancelar, basta avisar. Sem justificativa, sem complicação. O controle é seu.</p>
          </div>
        </div>
      </div>
    </div>
  </section>


  {/* ==========================================
       DOBRA 10 — BIO / AUTORIDADE
  ========================================== */}
  <section className="section-alt glow-side">
    <div className="container">
      <div className="section-header anim-fade-up">
        <span className="eyebrow eyebrow-lined">Quem criou</span>
        <h2>Feito por quem viveu o problema<br />na pele — e resolveu</h2>
      </div>

      <div className="autoridade-grid">
        <div className="autor-foto-wrap">
          <div className="autor-foto-ring-wrap">
            <div className="autor-ring"></div>
            <div className="autor-ring-2"></div>
            <div className="autor-foto-real">
              <img src={rodrigoFoto} alt="Rodrigo Haertel" loading="lazy" decoding="async" />
            </div>
          </div>

        </div>
        <div className="autor-info">
          <div className="autor-especialidade">Criador do Método do Custo ao Lucro</div>
          <div className="autor-nome">Rodrigo Haertel</div>
          <p className="autor-bio">Ex-sócio de rede de franquias, Rodrigo quase quebrou — não por falta de movimento, mas por falta de controle de margem. Operando na casa dos 5–6% de margem, ele reestruturou a operação do zero: mudou a forma de precificar, passou a controlar CMV ativamente e saiu para a casa dos 14–15% em menos de um ano. O método que nasceu dessa virada é o Dono 14%.</p>
          <p className="autor-bio">Com mais de 4.500 pessoas treinadas e 75h de conteúdo gratuito publicado, Rodrigo desenvolveu o Software Oficial do Dono 14% para colocar nas mãos de qualquer dono a ferramenta que ele mesmo precisou e não tinha.</p>
          <div className="autor-badges">
            <span className="autor-badge">Salvou a operação após quase quebrar</span>
            <span className="autor-badge">Facilitador do Empretec</span>
            <span className="autor-badge">Coautor do Empretec 2025</span>
            <span className="autor-badge">+4.500 pessoas treinadas</span>
            <span className="autor-badge">+75h de conteúdo gratuito</span>
            <span className="autor-badge">Criador do Método Custo ao Lucro</span>
          </div>
        </div>
      </div>
    </div>
  </section>


  {/* ==========================================
       DOBRA 11 — COMPARAÇÃO (mais agressiva)
  ========================================== */}
  <section className="comp-section glow-top">
    <div className="container">
      <div className="comp-header">
        <span className="eyebrow" style={{display: "inline-flex"}}><span className="eyebrow-dot"></span>A diferença</span>
        <h2>A diferença entre vender muito…<br />e lucrar de verdade.</h2>
        <p>Gestão não é luxo. É a diferença entre reagir ao problema — ou nunca ter o problema.</p>
      </div>

      <div className="comp-table">
        <div className="comp-table-header">
          <span style={{color: "var(--text-muted)"}}>O que muda</span>
          <span className="col-sem">Sem controle</span>
          <span className="col-com">Dono 14%</span>
        </div>

        <div className="comp-row">
          <div className="comp-row-label">
            <strong>Custo real por prato</strong>
            Você sabe quanto cada prato realmente custa?
          </div>
          <div className="comp-cell comp-cell--sem">✗</div>
          <div className="comp-cell comp-cell--com">✓</div>
        </div>

        <div className="comp-row">
          <div className="comp-row-label">
            <strong>Preço formado por margem</strong>
            Seu preço é definido por número ou por chute?
          </div>
          <div className="comp-cell comp-cell--sem">✗</div>
          <div className="comp-cell comp-cell--com">✓</div>
        </div>

        <div className="comp-row">
          <div className="comp-row-label">
            <strong>CMV monitorado em tempo real</strong>
            Você sabe se está dentro da meta agora?
          </div>
          <div className="comp-cell comp-cell--sem">✗</div>
          <div className="comp-cell comp-cell--com">✓</div>
        </div>

        <div className="comp-row">
          <div className="comp-row-label">
            <strong>Pratos vilões identificados</strong>
            Você sabe quais pratos estão te custando lucro?
          </div>
          <div className="comp-cell comp-cell--sem">✗</div>
          <div className="comp-cell comp-cell--com">✓</div>
        </div>

        <div className="comp-row">
          <div className="comp-row-label">
            <strong>Simulação antes de decidir</strong>
            Você testa o impacto antes de ajustar preço?
          </div>
          <div className="comp-cell comp-cell--sem">✗</div>
          <div className="comp-cell comp-cell--com">✓</div>
        </div>

        <div className="comp-row">
          <div className="comp-row-label">
            <strong>Fim de mês previsível</strong>
            Você sabe o que vai sobrar antes do mês fechar?
          </div>
          <div className="comp-cell comp-cell--sem">✗</div>
          <div className="comp-cell comp-cell--com">✓</div>
        </div>

      </div>
    </div>
  </section>


  {/* ==========================================
       DOBRA 12 — FAQ
  ========================================== */}
  <section className="section-dark">
    <div className="container--narrow">
      <div className="section-header anim-fade-up">
        <span className="eyebrow"><span className="eyebrow-dot"></span>Perguntas frequentes</span>
        <h2>Respondendo o que você<br />está pensando agora</h2>
      </div>

      <div style={{marginTop: "48px"}}>
        <div className="accordion-item">
          <div className="accordion-header"><span>Funciona para o meu tipo de restaurante?</span><span className="accordion-icon">+</span></div>
          <div className="accordion-body"><div className="accordion-body-inner">Sim. Funciona para delivery, restaurante físico, lanchonete, hamburgueria, pizzaria e similares. O cálculo é baseado em margem real — não no tipo de cozinha. Se você vende comida e quer saber quanto cada prato deixa no caixa, o sistema foi feito para você.</div></div>
        </div>
        <div className="accordion-item">
          <div className="accordion-header"><span>Tenho medo de mexer nos preços. O sistema vai me obrigar a aumentar?</span><span className="accordion-icon">+</span></div>
          <div className="accordion-body"><div className="accordion-body-inner">Não. O sistema mostra o impacto real da sua margem antes de qualquer decisão. Subir preço sem número é arriscado. Ajustar preço com margem validada é gestão. Você decide com segurança — o sistema não decide por você.</div></div>
        </div>
        <div className="accordion-item">
          <div className="accordion-header"><span>O software é complicado?</span><span className="accordion-icon">+</span></div>
          <div className="accordion-body"><div className="accordion-body-inner">Se você sabe cadastrar um produto no iFood, você sabe usar o sistema. E se tiver dúvida em qualquer parte, cada menu tem um vídeo de tutorial integrado — você assiste na hora certa, sem precisar buscar ajuda em outro lugar.</div></div>
        </div>
        <div className="accordion-item">
          <div className="accordion-header"><span>Eu já uso planilha. Vale a pena trocar?</span><span className="accordion-icon">+</span></div>
          <div className="accordion-body"><div className="accordion-body-inner">Se sua planilha já mostra margem real por prato, CMV atualizado automaticamente e simulação de cenário — talvez não precise. Mas se você ainda depende de fórmula manual, o sistema economiza tempo, reduz erro e entrega visão que planilha não consegue.</div></div>
        </div>
        <div className="accordion-item">
          <div className="accordion-header"><span>Posso cancelar quando quiser?</span><span className="accordion-icon">+</span></div>
          <div className="accordion-body"><div className="accordion-body-inner">Sim. Sem contrato. Sem multa. Sem burocracia. Se em algum momento você decidir cancelar, basta avisar. Simples assim.</div></div>
        </div>
        <div className="accordion-item">
          <div className="accordion-header"><span>Como funciona o acesso?</span><span className="accordion-icon">+</span></div>
          <div className="accordion-body"><div className="accordion-body-inner">Acesso imediato após a compra. Você recebe os dados de login por e-mail e pode começar a configurar seu primeiro prato no mesmo dia. Junto vem o tutorial completo e o suporte via WhatsApp.</div></div>
        </div>
      </div>

    </div>
  </section>


  {/* ==========================================
       CTA FINAL (único CTA de fechamento)
  ========================================== */}
  <section className="cta-final">
    <div className="container">
      <span className="eyebrow anim-fade-up" style={{display: "inline-flex", marginBottom: "40px"}}><span className="eyebrow-dot"></span>Chega de torcer para lucrar</span>

      <h2 className="anim-fade-up anim-delay-1">
        Você pode continuar torcendo…<br />
        <em>ou pode começar a controlar.</em>
      </h2>

      <p className="anim-fade-up anim-delay-2" style={{margin: "28px auto 0"}}>
        Por menos de R$ 4 por dia, você sabe exatamente quanto cada prato deixa no seu caixa.<br />Acesso imediato. Sem contrato. Cancele quando quiser.
      </p>

      <div className="cta-final-divider anim-fade-up anim-delay-3"></div>

      <div className="anim-fade-up anim-delay-3" style={{textAlign: "center"}}>
        <a href="https://pay.hotmart.com/G104668166T" className="btn btn-primary" style={{fontSize: "1.2rem", padding: "22px 64px"}}>
          Quero ver quanto cada prato realmente lucra →
        </a>
        <div className="trust-row" style={{marginTop: "24px", justifyContent: "center", gap: "28px"}}>
          <span className="trust-item">R$ 97/mês</span>
          <span className="trust-item">Acesso imediato</span>
          <span className="trust-item">Cancele quando quiser</span>
        </div>
      </div>

      <div className="anim-fade-up anim-delay-4" style={{marginTop: "72px", paddingTop: "56px", borderTop: "1px solid var(--border-subtle)"}}>
        <p className="cta-final-filosofia">
          Lucro não é sorte. É decisão baseada em número.
        </p>
        <span style={{fontFamily: "var(--font-b)", fontStyle: "normal", fontSize: "0.9rem", color: "var(--text-muted)", marginTop: "12px", display: "block"}}>— Rodrigo Haertel, criador do Método DCAL</span>
      </div>
    </div>
  </section>
      </div>

      {/* Sticky CTA — mobile only, aparece após scroll */}
      <div className="sp-sticky" id="sp-sticky">
        <a href="https://pay.hotmart.com/G104668166T" className="sp-sticky-btn">
          Começar por R$ 97/mês →
        </a>
        <p className="sp-sticky-trust">Acesso imediato · Cancele quando quiser · Suporte WhatsApp</p>
      </div>

      {/* Footer minimalista — fora do escopo .sistema-page para herdar tipografia padrão */}
      <footer style={{background:"hsl(165,60%,6%)", borderTop:"1px solid hsla(165,40%,25%,0.25)", padding:"24px 0"}}>
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-6 text-xs md:flex-row" style={{color:"hsl(165,40%,45%)"}}>
          <p>© {new Date().getFullYear()} — Todos os direitos reservados.</p>
          <p>Plano A Mentoria LTDA. CNPJ: 18.836.944/0001-69</p>
        </div>
      </footer>
    </>
  );
};

export default Sistema;

