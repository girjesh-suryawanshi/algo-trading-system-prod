import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-login',
  template: `
    <div class="auth-wrapper">
      <div class="auth-card glass">
        <div class="auth-header">
          <div class="logo">Lumina<span>Quant</span></div>
          <h2>Welcome Back</h2>
          <p>Login to your professional trading dashboard</p>
        </div>

        <form (ngSubmit)="onSubmit()" #loginForm="ngForm">
          <div class="form-group">
            <label>Email Address</label>
            <input type="email" name="email" [(ngModel)]="model.email" required placeholder="name@company.com">
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" [(ngModel)]="model.password" required placeholder="••••••••">
          </div>
          
          <button type="submit" class="btn-primary" [disabled]="loading">
            {{ loading ? 'Authenticating...' : 'Sign In' }}
          </button>
        </form>

        <div class="divider"><span>OR</span></div>

        <button class="btn-google" (click)="loginWithGoogle()">
          <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google">
          Continue with Google
        </button>

        <p class="auth-footer">Don't have an account? <a routerLink="/register">Create one</a></p>
      </div>
    </div>
  `,
  styles: [`
    .auth-wrapper {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at top right, #1a1b26, #0a0b10);
      font-family: 'Inter', sans-serif;
    }

    .auth-card {
      width: 100%;
      max-width: 450px;
      padding: 3rem;
      border-radius: 32px;
    }

    .glass {
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(24px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 40px 100px rgba(0,0,0,0.5);
    }

    .auth-header { text-align: center; margin-bottom: 2.5rem; }

    .logo {
      font-size: 1.5rem;
      font-weight: 800;
      margin-bottom: 1rem;
      color: white;
    }
    .logo span { color: #00f2ff; }

    h2 { font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; color: #fff; }
    p { color: #94a3b8; font-size: 0.95rem; }

    .form-group { margin-bottom: 1.5rem; }
    label { display: block; color: #cbd5e1; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; }

    input {
      width: 100%;
      padding: 1rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      color: white;
      font-size: 1rem;
      transition: 0.3s;
    }

    input:focus { outline: none; border-color: #00f2ff; box-shadow: 0 0 0 4px rgba(0, 242, 255, 0.1); }

    .btn-primary {
      width: 100%;
      padding: 1rem;
      background: linear-gradient(135deg, #00f2ff, #7000ff);
      border: none;
      border-radius: 12px;
      color: white;
      font-weight: 700;
      font-size: 1rem;
      cursor: pointer;
      margin-top: 1rem;
      transition: 0.3s;
    }

    .btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0, 242, 255, 0.2); }

    .divider { margin: 2rem 0; text-align: center; position: relative; }
    .divider::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: rgba(255,255,255,0.05); }
    .divider span { position: relative; background: #0c0d14; padding: 0 1rem; color: #475569; font-size: 0.8rem; font-weight: 700; z-index: 1; }

    .btn-google {
      width: 100%;
      padding: 1rem;
      background: white;
      color: #1f2937;
      border: none;
      border-radius: 12px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      cursor: pointer;
      transition: 0.3s;
    }

    .btn-google img { width: 20px; }
    .btn-google:hover { background: #f9fafb; transform: translateY(-2px); }

    .auth-footer { text-align: center; margin-top: 2rem; color: #64748b; }
    .auth-footer a { color: #00f2ff; text-decoration: none; font-weight: 700; }
  `]
})
export class LoginComponent {
  model: any = {};
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  onSubmit() {
    this.loading = true;
    this.auth.login(this.model).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err) => {
        alert('Invalid credentials');
        this.loading = false;
      }
    });
  }

  loginWithGoogle() {
      // Logic for Google OAuth redirect
      window.location.href = 'http://localhost:8080/oauth2/authorization/google';
  }
}
