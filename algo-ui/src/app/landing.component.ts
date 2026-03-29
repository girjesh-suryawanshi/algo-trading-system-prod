import { Component } from '@angular/core';

@Component({
  selector: 'app-landing',
  template: `
    <div class="landing-container">
      <nav class="navbar">
        <div class="logo">Lumina<span>Quant</span></div>
        <div class="nav-links">
          <a routerLink="/login" class="nav-item">Login</a>
          <a routerLink="/register" class="btn-primary">Get Started</a>
        </div>
      </nav>

      <section class="hero">
        <div class="hero-content">
          <h1>Master the Markets with <span>Autonomous Intelligence</span></h1>
          <p>The ultimate professional trading terminal for NIFTY & BankNIFTY. Precision execution, deep backtesting, and automated risk management at your fingertips.</p>
          <div class="cta-group">
            <button routerLink="/register" class="btn-hero">Start Trading Free</button>
            <button class="btn-secondary">Watch Demo</button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="glass-card preview-card">
            <div class="card-header">Live Market Signal</div>
            <div class="card-body">
              <div class="signal-row">
                <span>NIFTY CE 23500</span>
                <span class="status-badge">LOW DETECTED</span>
              </div>
              <div class="signal-row">
                <span>ENTRY</span>
                <span class="price">₹11.20</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="features">
        <div class="feature-card">
          <div class="icon">🚀</div>
          <h3>Live Terminal</h3>
          <p>Real-time strike selection and automated order slicing using Dhan API.</p>
        </div>
        <div class="feature-card">
          <div class="icon">📊</div>
          <h3>Backtest Lab</h3>
          <p>Simulate years of history in seconds with our high-performance rolling cloud engine.</p>
        </div>
        <div class="feature-card">
          <div class="icon">🛡️</div>
          <h3>Risk Governance</h3>
          <p>Institutional-grade kill switches and position monitoring to protect your capital.</p>
        </div>
      </section>
    </div>
  `,
  styles: [`
    :host {
      --primary: #00f2ff;
      --secondary: #7000ff;
      --dark: #0a0b10;
      --glass: rgba(255, 255, 255, 0.05);
      --glass-border: rgba(255, 255, 255, 0.1);
      display: block;
      background: var(--dark);
      color: white;
      min-height: 100vh;
      font-family: 'Inter', sans-serif;
    }

    .landing-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 2rem;
    }

    .navbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 2rem 0;
    }

    .logo {
      font-size: 1.5rem;
      font-weight: 800;
      letter-spacing: -1px;
    }

    .logo span { color: var(--primary); }

    .nav-links { display: flex; gap: 2rem; align-items: center; }

    .nav-item { color: #888; text-decoration: none; transition: 0.3s; }
    .nav-item:hover { color: white; }

    .btn-primary {
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      padding: 0.8rem 1.5rem;
      border-radius: 12px;
      text-decoration: none;
      color: white;
      font-weight: 600;
      box-shadow: 0 10px 20px rgba(0, 242, 255, 0.2);
    }

    .hero {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 4rem;
      padding: 6rem 0;
      align-items: center;
    }

    h1 {
      font-size: 4.5rem;
      line-height: 1.1;
      font-weight: 900;
      margin-bottom: 1.5rem;
    }

    h1 span {
      background: linear-gradient(to right, var(--primary), var(--secondary));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    p {
      font-size: 1.25rem;
      color: #94a3b8;
      line-height: 1.6;
      margin-bottom: 2.5rem;
    }

    .cta-group { display: flex; gap: 1.5rem; }

    .btn-hero {
      background: white;
      color: var(--dark);
      border: none;
      padding: 1.2rem 2.5rem;
      border-radius: 12px;
      font-weight: 700;
      font-size: 1.1rem;
      cursor: pointer;
      transition: 0.3s;
    }

    .btn-hero:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(255,255,255,0.1); }

    .btn-secondary {
      background: transparent;
      border: 1px solid var(--glass-border);
      color: white;
      padding: 1.2rem 2.5rem;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
    }

    .glass-card {
      background: var(--glass);
      backdrop-filter: blur(20px);
      border: 1px solid var(--glass-border);
      border-radius: 24px;
      padding: 2rem;
    }

    .preview-card {
      transform: perspective(1000px) rotateY(-15deg);
      box-shadow: 20px 40px 60px rgba(0,0,0,0.5);
    }

    .card-header { font-size: 0.9rem; color: #888; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 1px; }

    .signal-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }

    .status-badge { background: rgba(0, 242, 255, 0.1); color: var(--primary); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }

    .price { font-size: 1.5rem; font-weight: 800; color: #fff; }

    .features {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2rem;
      margin: 4rem 0;
    }

    .feature-card {
      background: var(--glass);
      padding: 3rem;
      border-radius: 32px;
      border: 1px solid var(--glass-border);
      transition: 0.3s;
    }

    .feature-card:hover { border-color: var(--primary); transform: translateY(-10px); }

    .icon { font-size: 2.5rem; margin-bottom: 1.5rem; }

    h3 { font-size: 1.5rem; margin-bottom: 1rem; }

    .feature-card p { font-size: 1rem; margin-bottom: 0; }
  `]
})
export class LandingComponent {}
