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

            <!-- General Info -->
            <div class="section">
              <h3>General Information</h3>
              <div class="form-group">
                <label>Full Name</label>
                <input type="text" name="name" [(ngModel)]="profile.name" placeholder="Enter your name">
              </div>
            </div>

            <!-- Dhan -->
            <div class="section">
              <h3>Dhan Exchange Connection</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Dhan Client ID</label>
                  <input type="text" name="dhanClientId" [(ngModel)]="profile.dhanClientId">
                </div>
                <div class="form-group">
                  <label>Dhan Access Token</label>
                  <input type="password" name="dhanAccessToken" [(ngModel)]="profile.dhanAccessToken">
                </div>
              </div>
            </div>

            <!-- Telegram -->
            <div class="section">
              <h3>Telegram Notifications</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Bot Token</label>
                  <input type="password" name="telegramBotToken" [(ngModel)]="profile.telegramBotToken">
                </div>
                <div class="form-group">
                  <label>Chat ID</label>
                  <input type="text" name="telegramChatId" [(ngModel)]="profile.telegramChatId">
                </div>
              </div>
            </div>

            <!-- Risk -->
            <div class="section">
              <h3>Risk & TSL Management</h3>
              <p class="form-help mb-3">Safety limits enforced at backend.</p>

              <div class="form-row">
                <div class="form-group">
                  <label>Max Daily Loss (₹)</label>
                  <input type="number" name="maxDailyLoss" [(ngModel)]="profile.maxDailyLoss">
                </div>
                <div class="form-group">
                  <label>Max Trades Per Day</label>
                  <input type="number" name="maxTradesPerDay" [(ngModel)]="profile.maxTradesPerDay">
                </div>
              </div>

              <!-- ✅ FIXED BLOCK -->
              <div class="form-row">
                <div class="form-group">
                  <label>Trailing SL Step (₹)</label>
                  <input type="number" step="0.5" name="trailingStopLossStep" [(ngModel)]="profile.trailingStopLossStep">
                </div>
                <div class="form-group">
                  <label>Target Price Limit</label>
                  <input type="number" name="targetPriceLimit" [(ngModel)]="profile.targetPriceLimit">
                </div>
              </div>
            </div>

            <!-- Market Safety -->
            <div class="section">
              <h3>Market Safety Guards</h3>

              <div class="form-row">
                <div class="form-group">
                  <label>India VIX Threshold</label>
                  <input type="number" name="vixThreshold" [(ngModel)]="profile.vixThreshold">
                </div>
                <div class="form-group">
                  <label>News Buffer (Minutes)</label>
                  <input type="number" name="newsBufferMinutes" [(ngModel)]="profile.newsBufferMinutes">
                </div>
              </div>

              <div class="form-group">
                <label>
                  <input type="checkbox" name="newsKillSwitchActive" [(ngModel)]="profile.newsKillSwitchActive">
                  Enable News Kill Switch
                </label>
              </div>
            </div>

            <!-- Footer -->
            <div class="footer">
              <button type="submit" class="btn-save" [disabled]="loading">
                {{ loading ? 'Saving...' : 'Save Configuration' }}
              </button>
            </div>

          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      background: #0a0b10;
      min-height: 100vh;
      color: white;
      font-family: sans-serif;
    }
    .profile-container { max-width: 900px; margin: auto; padding: 2rem; }
    .form-row { display: flex; gap: 1rem; }
    .form-group { flex: 1; margin-bottom: 1rem; }
    input { width: 100%; padding: 10px; }
    .btn-save { padding: 10px 20px; }
  `]
})
export class ProfileComponent implements OnInit {

  profile: any = {
    newsKillSwitchActive: true
  };

  loading = false;

  private baseUrl = `${window.location.protocol}//${window.location.hostname}:8080/api/user`;

  constructor(private http: HttpClient, private router: Router) { }

  ngOnInit() {
    this.loadProfile();
  }

  loadProfile() {
    this.http.get(`${this.baseUrl}/profile`).subscribe({
      next: (data: any) => this.profile = data,
      error: () => alert('Failed to load profile')
    });
  }

  saveProfile() {
    this.loading = true;

    this.http.put(`${this.baseUrl}/profile`, this.profile).subscribe({
      next: () => {
        alert('Saved successfully');
        this.loading = false;
      },
      error: () => {
        alert('Save failed');
        this.loading = false;
      }
    });
  }
}