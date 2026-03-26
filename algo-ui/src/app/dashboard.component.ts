import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  template: `
  <div class="dashboard dark-theme">
    <header>
      <h1>Algo Trading Terminal</h1>
      <div class="status-panel">
        <button [class.active]="killSwitch" (click)="toggleKillSwitch()">
          {{ killSwitch ? 'DEACTIVATE KILL SWITCH' : 'ACTIVATE KILL SWITCH' }}
        </button>
      </div>
    </header>

    <div class="metrics-grid">
      <div class="card">
        <h3>Win Rate</h3>
        <p class="value">{{ winRate }}%</p>
      </div>
      <div class="card">
        <h3>Total PnL</h3>
        <p class="value" [class.green]="totalPnL > 0" [class.red]="totalPnL < 0">
          ₹{{ totalPnL }}
        </p>
      </div>
      <div class="card">
        <h3>Active Trades</h3>
        <p class="value">{{ activeTradesCount }}</p>
      </div>
    </div>

    <div class="main-content">
      <div class="trade-table">
        <h2>Live Trades</h2>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Symbol</th>
              <th>Strike</th>
              <th>Type</th>
              <th>Entry</th>
              <th>Exit</th>
              <th>PnL</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let t of trades">
              <td>{{ t.createdAt | date:'HH:mm:ss' }}</td>
              <td>{{ t.symbol }}</td>
              <td>{{ t.strike }}</td>
              <td>{{ t.optionType }}</td>
              <td>₹{{ t.entryPrice }}</td>
              <td>{{ t.exitPrice ? '₹'+t.exitPrice : '-' }}</td>
              <td [class.green]="t.pnl > 0" [class.red]="t.pnl < 0">
                {{ t.pnl ? '₹'+t.pnl : '-' }}
              </td>
              <td><span class="badge" [attr.data-status]="t.status">{{ t.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  `,
  styles: [`
    .dark-theme {
      background: #0f172a;
      color: #f8fafc;
      min-height: 100vh;
      padding: 20px;
      font-family: 'Inter', sans-serif;
    }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
    .metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
    .card { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
    .card h3 { margin: 0; font-size: 0.9rem; color: #94a3b8; }
    .value { font-size: 1.8rem; font-weight: bold; margin: 10px 0 0; }
    .green { color: #10b981; }
    .red { color: #ef4444; }
    table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
    th, td { padding: 15px; text-align: left; border-bottom: 1px solid #334155; }
    th { color: #94a3b8; font-weight: 500; }
    .badge { padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge[data-status='OPEN'] { background: #0369a1; }
    .badge[data-status='TARGET_HIT'] { background: #065f46; }
    .badge[data-status='SL_HIT'] { background: #991b1b; }
    button { padding: 10px 20px; border-radius: 8px; border: none; background: #ef4444; color: white; cursor: pointer; font-weight: bold; }
    button.active { background: #10b981; }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy {
  trades: any[] = [];
  killSwitch = false;
  winRate = 0;
  totalPnL = 0;
  activeTradesCount = 0;
  private sub?: Subscription;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.refreshData();
    this.sub = interval(3000).subscribe(() => this.refreshData());
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  refreshData() {
    this.http.get<any[]>('http://localhost:8080/api/trades').subscribe(res => {
      this.trades = res.reverse();
      this.calculateMetrics();
    });
  }

  calculateMetrics() {
    const closed = this.trades.filter(t => t.status !== 'OPEN');
    if (closed.length > 0) {
      const wins = closed.filter(t => t.pnl > 0).length;
      this.winRate = Math.round((wins / closed.length) * 100);
      this.totalPnL = Math.round(closed.reduce((acc, t) => acc + (t.pnl || 0), 0));
    }
    this.activeTradesCount = this.trades.filter(t => t.status === 'OPEN').length;
  }

  toggleKillSwitch() {
    this.killSwitch = !this.killSwitch;
    this.http.post(`http://localhost:8080/api/kill?active=${this.killSwitch}`, {}).subscribe();
  }
}
