import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';
import { AuthService } from './auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  styleUrls: ['./dashboard.component.css'],
  template: `
  <div class="dashboard dark-theme">
    <header class="glass-header">
      <div class="brand">
        <h1>Lumina<span class="neon-text">Quant</span></h1>
      </div>
      
      <div class="tabs">
        <button [class.active-tab]="activeTab === 'LIVE'" (click)="activeTab = 'LIVE'">LIVE TERMINAL</button>
        <button [class.active-tab]="activeTab === 'BACKTEST'" (click)="activeTab = 'BACKTEST'">BACKTEST LAB</button>
      </div>

      <div class="status-panel">
        <div class="user-info">
          <button routerLink="/profile" class="btn-profile">Settings</button>
          <button (click)="onLogout()" class="btn-logout">Logout</button>
        </div>
        <button *ngIf="activeTab === 'LIVE'" [class.active-neon]="autoRunning" [class.inactive-neon]="!autoRunning" (click)="toggleEngine()">
          ENGINE: {{ autoRunning ? 'LIVE' : 'IDLE' }}
        </button>
      </div>
    </header>

    <!-- LIVE TERMINAL VIEW -->
    <div *ngIf="activeTab === 'LIVE'" class="main-grid">
      <!-- LEFT COLUMN -->
      <div class="left-col">
        <!-- STRATEGY TRACKER -->
        <div class="glass-card">
          <h2><i class="icon">⚡</i> Active Tracking</h2>
          <div class="tracker-list">
            <div *ngIf="!hasTrackedStrikes()" class="empty-state">No strikes currently matching criteria (Premium <= 12).</div>
            <div *ngFor="let kv of getTrackedStrikes()" class="track-item" [class.executed]="kv.value.status === 'EXECUTED'">
              <div class="track-header">
                <span class="opt-badge" [class.ce]="kv.key === 'CE'" [class.pe]="kv.key === 'PE'">{{ kv.key }}</span>
                <strong>{{ kv.value.strike }}</strong>
                <span class="status-pill">{{ kv.value.status }}</span>
              </div>
              <div class="track-details">
                <div class="detail-box">
                  <small>LTP Low</small>
                  <span>₹{{ kv.value.low | number:'1.2-2' }}</span>
                </div>
                <div class="detail-box">
                  <small>Target Entry</small>
                  <span class="neon-text">₹{{ kv.value.entry | number:'1.2-2' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- MANUAL TRADE ENTRY -->
        <div class="glass-card mt-20">
          <h2><i class="icon">🎯</i> Manual Order</h2>
          <form (ngSubmit)="submitManualTrade()" class="manual-form">
            <div class="form-row">
              <div class="form-group">
                <label>Symbol</label>
                <input type="text" [(ngModel)]="manualTrade.symbol" name="symbol" required>
              </div>
              <div class="form-group">
                <label>Option Type</label>
                <select [(ngModel)]="manualTrade.optionType" name="opttype" required>
                  <option value="CE">CE</option>
                  <option value="PE">PE</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>Strike</label>
              <input type="number" [(ngModel)]="manualTrade.strike" name="strike" required>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Entry Price</label>
                <input type="number" [(ngModel)]="manualTrade.entryPrice" name="entry" required>
              </div>
              <div class="form-group">
                <label>Qty (Lots)</label>
                <input type="number" [(ngModel)]="manualTrade.qty" name="qty" required>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Stop Loss</label>
                <input type="number" [(ngModel)]="manualTrade.stopLoss" name="sl" required>
              </div>
              <div class="form-group">
                <label>Target</label>
                <input type="number" [(ngModel)]="manualTrade.target1" name="target" required>
              </div>
            </div>
            <button type="submit" class="submit-btn" [disabled]="isSubmitting">
              {{ isSubmitting ? 'SENDING...' : 'EXECUTE TRADE' }}
            </button>
          </form>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="right-col">
        <!-- KPI METRICS -->
        <div class="metrics-grid">
          <div class="glass-card kpi">
            <h3>Win Rate</h3>
            <p class="value gradient-text">{{ winRate }}%</p>
          </div>
          <div class="glass-card kpi">
            <h3>Total PnL</h3>
            <p class="value" [class.neon-green]="totalPnL > 0" [class.neon-red]="totalPnL < 0">
              ₹{{ totalPnL }}
            </p>
          </div>
          <div class="glass-card kpi">
            <h3>Active Trades</h3>
            <p class="value">{{ activeTradesCount }}</p>
          </div>
        </div>

        <!-- LIVE TRADES TABLE -->
        <div class="glass-card trade-table-container mt-20">
          <h2><i class="icon">📊</i> Trade Ledger</h2>
          <table class="modern-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Instrument</th>
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
                <td><strong>{{ t.symbol }}</strong> <span>{{ t.strike }}</span></td>
                <td><span class="opt-badge small" [class.ce]="t.optionType === 'CE'" [class.pe]="t.optionType === 'PE'">{{ t.optionType }}</span></td>
                <td>₹{{ t.entryPrice }}</td>
                <td>{{ t.exitPrice ? '₹'+t.exitPrice : '-' }}</td>
                <td [class.neon-green]="t.pnl > 0" [class.neon-red]="t.pnl < 0">
                  <strong>{{ t.pnl ? '₹'+t.pnl : '-' }}</strong>
                </td>
                <td><span class="status-glow" [attr.data-status]="t.status">{{ t.status }}</span></td>
              </tr>
              <tr *ngIf="trades.length === 0">
                <td colspan="7" class="empty-state text-center">No trades executed today.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- BACKTEST LAB VIEW -->
    <div *ngIf="activeTab === 'BACKTEST'" class="main-grid">
      <div class="left-col">
        <div class="glass-card">
          <h2><i class="icon">🧪</i> Simulator settings</h2>
          <form (ngSubmit)="runBacktest()" class="manual-form">
            <div class="form-row">
              <div class="form-group">
                <label>From Date (YYYY-MM-DD)</label>
                <input type="text" [(ngModel)]="backtestReq.fromDate" name="fromDate" placeholder="2024-03-01" required>
              </div>
              <div class="form-group">
                <label>To Date (YYYY-MM-DD)</label>
                <input type="text" [(ngModel)]="backtestReq.toDate" name="toDate" placeholder="2024-03-05" required>
              </div>
            </div>
            <button type="submit" class="submit-btn" [disabled]="isBacktesting">
              {{ isBacktesting ? 'FETCHING & SIMULATING...' : 'RUN SIMULATION' }}
            </button>
          </form>
          <div *ngIf="backtestError" class="mt-20 neon-red text-center" style="font-weight: 500;">
            {{ backtestError }}
          </div>
          <div *ngIf="!backtestResults && !isBacktesting && !backtestError" class="empty-state mt-20 text-center">
            Ready to fetch historical rollingoption data.
          </div>
        </div>
      </div>
      
      <div class="right-col" *ngIf="backtestResults">
        <div class="metrics-grid">
          <div class="glass-card kpi">
            <h3>Win Rate</h3>
            <p class="value gradient-text">{{ backtestResults.metrics?.win_rate || '0%' }}</p>
          </div>
          <div class="glass-card kpi">
            <h3>Total PnL</h3>
            <p class="value neon-green">₹{{ backtestResults.metrics?.total_pnl || 0 }}</p>
          </div>
          <div class="glass-card kpi">
            <h3>Total Trades</h3>
            <p class="value">{{ backtestResults.metrics?.total_trades || 0 }}</p>
          </div>
        </div>

        <div class="glass-card trade-table-container mt-20">
          <h2><i class="icon">📊</i> Simulation Ledger</h2>
          <table class="modern-table">
            <thead>
              <tr>
                <th>Entry Time</th>
                <th>Exit Time</th>
                <th>Strike</th>
                <th>Type</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Target Hits</th>
                <th>PnL</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let t of backtestResults.trades">
                <td>{{ t.entry_time | slice:11:19 }}</td>
                <td>{{ t.exit_time | slice:11:19 || '-' }}</td>
                <td><strong>{{ t.strike }}</strong></td>
                <td><span class="opt-badge small" [class.ce]="t.optionType === 'CE'" [class.pe]="t.optionType === 'PE'">{{ t.optionType }}</span></td>
                <td>₹{{ t.entry }}</td>
                <td>{{ t.exit_price ? '₹'+t.exit_price : '-' }}</td>
                <td><span class="status-glow" [attr.data-status]="t.result">{{ t.result }}</span></td>
                <td [class.neon-green]="t.pnl > 0" [class.neon-red]="t.pnl < 0">
                  <strong>₹{{ t.pnl | number:'1.2-2' }}</strong>
                </td>
              </tr>
              <tr *ngIf="!backtestResults.trades || backtestResults.trades.length === 0">
                <td colspan="8" class="empty-state text-center">No trades triggered in this simulation period.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  `
})
export class DashboardComponent implements OnInit, OnDestroy {
  activeTab: 'LIVE' | 'BACKTEST' = 'LIVE';
  
  // Trading Data
  trades: any[] = [];
  killSwitch = false;
  winRate = 0;
  totalPnL = 0;
  activeTradesCount = 0;
  
  // Python Engine Tracking Data
  autoRunning = false;
  strategyState: any = {};
  
  // Manual Form State
  isSubmitting = false;
  manualTrade = {
    symbol: 'NIFTY',
    optionType: 'CE',
    strike: null as number | null,
    entryPrice: null as number | null,
    qty: 50,
    stopLoss: null as number | null,
    target1: null as number | null
  };
  
  // Backtest Module State
  isBacktesting = false;
  backtestError: string | null = null;
  backtestReq = {
    fromDate: '2024-03-01',
    toDate: '2024-03-05'
  };
  backtestResults: any = null;

  private sub?: Subscription;

  constructor(private http: HttpClient, private auth: AuthService, private router: Router) {}

  onLogout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  ngOnInit() {
    this.refreshData();
    this.sub = interval(3000).subscribe(() => this.refreshData());
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  refreshData() {
    if (this.activeTab !== 'LIVE') return; // Pause polling if in backtest view
    
    this.http.get<any[]>('http://localhost:8080/api/trades').subscribe({
      next: (res) => {
        this.trades = res.reverse();
        this.calculateMetrics();
      },
      error: () => {}
    });

    this.http.get<any>('http://localhost:8080/api/engine/status').subscribe({
      next: (res) => {
        this.autoRunning = res.auto_running;
        this.strategyState = res.strategy_state || {};
      },
      error: () => {}
    });
  }

  calculateMetrics() {
    const closed = this.trades.filter(t => t.status !== 'OPEN');
    if (closed.length > 0) {
      const wins = closed.filter(t => (t.pnl || 0) > 0).length;
      this.winRate = Math.round((wins / closed.length) * 100);
      this.totalPnL = Math.round(closed.reduce((acc, t) => acc + (t.pnl || 0), 0));
    } else {
      this.winRate = 0;
      this.totalPnL = 0;
    }
    this.activeTradesCount = this.trades.filter(t => t.status === 'OPEN').length;
  }

  toggleKillSwitch() {
    this.killSwitch = !this.killSwitch;
    this.http.post(`http://localhost:8080/api/kill?active=${this.killSwitch}`, {}).subscribe();
  }

  toggleEngine() {
    const nextState = !this.autoRunning;
    this.http.post(`http://localhost:8080/api/engine/toggle?active=${nextState}`, {}).subscribe({
      next: () => {
        this.autoRunning = nextState;
      },
      error: (err) => {
        alert("Failed to toggle engine. Check your Profile API keys.");
      }
    });
  }

  hasTrackedStrikes(): boolean {
    return Object.keys(this.strategyState).length > 0;
  }

  getTrackedStrikes() {
    return Object.keys(this.strategyState).map(key => ({
      key,
      value: this.strategyState[key]
    }));
  }

  submitManualTrade() {
    if (!this.manualTrade.strike || !this.manualTrade.entryPrice) return;
    this.isSubmitting = true;
    
    const payload = {
        symbol: this.manualTrade.symbol,
        strike: this.manualTrade.strike,
        optionType: this.manualTrade.optionType,
        entryPrice: this.manualTrade.entryPrice,
        stopLoss: this.manualTrade.stopLoss,
        target1: this.manualTrade.target1,
        qty: this.manualTrade.qty,
        strategyName: "Manual"
    };

    this.http.post('http://localhost:8080/api/trade', payload).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.manualTrade.strike = null;
        this.manualTrade.entryPrice = null;
        this.manualTrade.stopLoss = null;
        this.manualTrade.target1 = null;
        this.refreshData(); 
      },
      error: () => {
        this.isSubmitting = false;
        alert("Failed to execute trade. Check constraints.");
      }
    });
  }

  runBacktest() {
    if (!this.backtestReq.fromDate || !this.backtestReq.toDate) return;
    this.isBacktesting = true;
    this.backtestError = null;
    this.backtestResults = null;
    
    this.http.post<any>('http://localhost:8080/api/backtest/run', this.backtestReq).subscribe({
      next: (res) => {
        this.isBacktesting = false;
        if (res.error) {
          this.backtestError = res.error;
        } else {
          this.backtestResults = res;
        }
      },
      error: (err) => {
        this.isBacktesting = false;
        this.backtestError = "Failed to reach backend proxy. Ensure your Profile is configured.";
      }
    });
  }
}
