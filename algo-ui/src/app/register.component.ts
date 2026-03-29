import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-register',
  template: `
    <div class="auth-wrapper">
      <div class="auth-card glass">
        <div class="auth-header">
          <div class="logo">Lumina<span>Quant</span></div>
          <h2>Create Account</h2>
          <p>Join the future of professional algorithmic trading</p>
        </div>

        <form (ngSubmit)="onSubmit()" #registerForm="ngForm">
          <div class="form-group">
            <label>Full Name</label>
            <input type="text" name="name" [(ngModel)]="model.name" required placeholder="John Doe">
          </div>
          <div class="form-group">
            <label>Email Address</label>
            <input type="email" name="email" [(ngModel)]="model.email" required placeholder="name@company.com">
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" [(ngModel)]="model.password" required placeholder="••••••••">
          </div>
          
          <button type="submit" class="btn-primary" [disabled]="loading">
            {{ loading ? 'Creating Account...' : 'Sign Up' }}
          </button>
        </form>

        <p class="auth-footer">Already have an account? <a routerLink="/login">Sign In</a></p>
      </div>
    </div>
  `,
  styles: [`
    .auth-wrapper {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at top left, #1a1b26, #0a0b10);
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

    .auth-footer { text-align: center; margin-top: 2rem; color: #64748b; }
    .auth-footer a { color: #00f2ff; text-decoration: none; font-weight: 700; }
  `]
})
export class RegisterComponent {
  model: any = {};
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  onSubmit() {
    this.loading = true;
    this.auth.register(this.model).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err) => {
        alert('Failed to register');
        this.loading = false;
      }
    });
  }
}
