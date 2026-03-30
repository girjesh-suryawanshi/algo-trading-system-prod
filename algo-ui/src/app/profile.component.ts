import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-profile',
  template: `
    <div class="profile-container">
      <nav class="top-nav">
        <div class="logo">Lumina<span>Quant</span> Profile</div>
        <button routerLink="/dashboard" class="btn-back">← Back to Dashboard</button>
      </nav>

      <div class="content-wrapper">
        <div class="glass-card settings-card">
          <h2>API Configuration</h2>
          <p class="subtitle">Securely manage your Dhan and Telegram credentials. All keys are encrypted before storage.</p>

          <form (ngSubmit)="saveProfile()">
            <div class="section">
              <h3>General Information</h3>
              <div class="form-group">
                <label>Full Name</label>
                <input type="text" name="name" [(ngModel)]="profile.name" placeholder="Enter your name">
              </div>
            </div>

            <div class="section">
              <h3>Dhan Exchange Connection</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Dhan Client ID</label>
                  <input type="text" name="dhanClientId" [(ngModel)]="profile.dhanClientId" placeholder="Enter Client ID">
                </div>
                <div class="form-group">
                  <label>Dhan Access Token</label>
                  <input type="password" name="dhanAccessToken" [(ngModel)]="profile.dhanAccessToken" placeholder="Enter Access Token">
                </div>
              </div>
            </div>

            <div class="section">
              <h3>Telegram Notifications</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Bot Token</label>
                  <input type="password" name="telegramBotToken" [(ngModel)]="profile.telegramBotToken" placeholder="Enter Bot Token">
                </div>
                <div class="form-group">
                  <label>Chat ID</label>
                  <input type="text" name="telegramChatId" [(ngModel)]="profile.telegramChatId" placeholder="Enter Chat ID">
                </div>
              </div>
            </div>

            <div class="section">
              <h3>Strategy Settings</h3>
              <div class="form-group">
                <label>Scan Target Price Limit (e.g. 12.0 or 20.0)</label>
                <input type="number" name="targetPriceLimit" [(ngModel)]="profile.targetPriceLimit" placeholder="12.0">
                <p class="form-help">Option premiums at or below this price will be scanned for setup entry.</p>
              </div>
            </div>

            <div class="footer">
              <button type="submit" class="btn-save" [disabled]="loading">
                {{ loading ? 'Saving Changes...' : 'Save Configuration' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      --primary: #00f2ff;
      --dark: #0a0b10;
      --glass: rgba(255, 255, 255, 0.03);
      --glass-border: rgba(255, 255, 255, 0.1);
      display: block;
      background: radial-gradient(circle at top right, #1a1b26, #0a0b10);
      min-height: 100vh;
      color: white;
      font-family: 'Inter', sans-serif;
    }

    .profile-container { max-width: 900px; margin: 0 auto; padding: 2rem; }
    .top-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3rem; }
    .logo { font-weight: 800; font-size: 1.2rem; }
    .logo span { color: var(--primary); }
    .btn-back { background: transparent; border: 1px solid var(--glass-border); color: #888; padding: 0.6rem 1rem; border-radius: 8px; cursor: pointer; transition: 0.3s; }
    .btn-back:hover { color: white; border-color: white; }
    .glass-card { background: var(--glass); backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-radius: 24px; padding: 3rem; }
    h2 { font-size: 2rem; margin-bottom: 0.5rem; }
    .subtitle { color: #94a3b8; margin-bottom: 3rem; }
    .section { margin-bottom: 3rem; padding-bottom: 2rem; border-bottom: 1px solid var(--glass-border); }
    h3 { font-size: 1.1rem; color: var(--primary); margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 1px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    .form-group { margin-bottom: 1.5rem; }
    label { display: block; color: #cbd5e1; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
    input, select {
      width: 100%;
      padding: 1rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      color: white;
      font-size: 0.9rem;
      transition: 0.3s;
    }
    input:focus, select:focus { outline: none; border-color: var(--primary); }
    select option { background: #1a1b26; color: white; }
    .form-help { font-size: 0.75rem; color: #64748b; margin-top: 0.4rem; }
    .btn-save {
      background: linear-gradient(135deg, var(--primary), #7000ff);
      color: white;
      border: none;
      padding: 1.2rem 2.5rem;
      border-radius: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: 0.3s;
    }
    .btn-save:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0, 242, 255, 0.2); }
  `]
})
export class ProfileComponent implements OnInit {
  profile: any = {};
  loading = false;


  private baseUrl = `${window.location.protocol}//${window.location.hostname}:8080/api/user`;

  constructor(private http: HttpClient, private router: Router) {}

  ngOnInit() {
    this.loadProfile();
  }

  loadProfile() {
    this.http.get(`${this.baseUrl}/profile`).subscribe({
      next: (data: any) => {
        this.profile = data;
      },
      error: () => alert('Failed to load profile')
    });
  }

  saveProfile() {
    this.loading = true;
    this.http.put(`${this.baseUrl}/profile`, this.profile).subscribe({
      next: () => {
        alert('Profile saved successfully');
        this.loading = false;
        this.loadProfile();
      },
      error: (err) => {
        const msg = err.error?.message || err.statusText || 'Unknown error';
        alert('Failed to save profile: ' + msg);
        this.loading = false;
      }
    });
  }
}
