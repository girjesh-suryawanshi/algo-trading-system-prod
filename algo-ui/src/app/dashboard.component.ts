import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';
import { AuthService } from './auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  styleUrls: ['./dashboard.component.css'],
  template: `
  <div class="dashboard-container">
    <!-- LEFT SIDEBAR -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="logo-text">Lumina<span class="logo-accent">Quant</span></span>
      </div>

      <nav class="nav-groups">
        <div class="nav-group">
          <div class="group-label">Trading Console</div>
          <button class="nav-item" [class.active]="currentView === 'TERMINAL'" (click)="currentView = 'TERMINAL'">
            🖥️ Terminal Monitor
          </button>
          <button class="nav-item" [class.active]="currentView === 'OPTION_CHAIN'" (click)="currentView = 'OPTION_CHAIN'">
            ⛓️ Option Chain
          </button>
          <button class="nav-item" [class.active]="currentView === 'LEDGER'" (click)="currentView = 'LEDGER'">
            📊 Trade Ledger
          </button>
        </div>

        <div class="nav-group">
          <div class="group-label">Analysis</div>
          <button class="nav-item" [class.active]="currentView === 'BACKTEST'" (click)="currentView = 'BACKTEST'">
            🧪 Backtest Lab
          </button>
        </div>

        <div class="nav-group">
          <div class="group-label">Account Management</div>
          <button class="nav-item" (click)="router.navigate(['/profile'])">
            ⚙️ Settings
          </button>
          <button class="nav-item" (click)="onLogout()">
            🚪 Logout
          </button>
        </div>
      </nav>
    </aside>

    <!-- RIGHT MAIN STAGE -->
    <main class="main-stage">
      <!-- NAVBAR -->
      <nav class="navbar">
        <div class="view-title">{{ currentView }}</div>

        <div class="nav-actions">
          <div class="market-selector">
            <select [(ngModel)]="selectedInstrument" (change)="onInstrumentChange(selectedInstrument)" [disabled]="autoRunning">
              <option *ngFor="let inst of getInstrumentList()" [value]="inst">{{ inst }}</option>
            </select>
            <select [(ngModel)]="selectedExpiry" [disabled]="autoRunning || loadingExpiries || expiries.length === 0">
               <option value="">{{ loadingExpiries ? 'Fetching...' : (expiries.length === 0 ? 'No Expiry' : 'Select Expiry') }}</option>
               <option *ngFor="let exp of expiries" [value]="exp">{{ exp }}</option>
            </select>
          </div>

          <div class="engine-status" [class.live]="autoRunning" [class.idle]="!autoRunning" (click)="toggleEngine()">
            <span class="status-dot" [class.pulse]="autoRunning"></span>
            ENGINE: {{ autoRunning ? 'LIVE' : 'IDLE' }}
          </div>
        </div>
      </nav>

      <!-- CONTENT BODY -->
      <section class="content-body">
        
        <!-- TERMINAL VIEW (Default) -->
        <div *ngIf="currentView === 'TERMINAL'">
          <div class="kpi-grid">
            <div class="glass-card kpi-card">
              <small class="text-muted">Daily PnL</small>
              <div class="kpi-value" [class.neon-green]="totalPnL > 0" [class.neon-red]="totalPnL < 0">₹{{ totalPnL }}</div>
            </div>
            <div class="glass-card kpi-card">
              <small class="text-muted">Win Rate</small>
              <div class="kpi-value neon-blue">{{ winRate }}%</div>
            </div>
            <div class="glass-card kpi-card">
              <small class="text-muted">India VIX</small>
              <div class="kpi-value" [class.neon-red]="indiaVix > vixThreshold">{{ indiaVix | number:'1.2-2' }}</div>
            </div>
            <div class="glass-card kpi-card">
              <small class="text-muted">Trades Today</small>
              <div class="kpi-value">{{ trades.length }}</div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 340px; gap: 24px;">
            <div class="glass-card">
              <h3>Active Tracking</h3>
              <div class="tracker-list mt-20">
                <div *ngIf="getTrackedStrikes().length === 0" class="empty-state">Wait... Engine is searching for entries based on your strategy.</div>
                <div *ngFor="let kv of getTrackedStrikes()" class="track-item" style="border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                   <div style="display: flex; justify-content: space-between; align-items: center;">
                      <strong>{{ kv.key }}: {{ kv.value.strike }}</strong>
                      <span [style.color]="kv.value.status === 'EXECUTED' ? '#10b981' : '#94a3b8'">{{ kv.value.status }}</span>
                   </div>
                   <div style="font-size: 0.8rem; margin-top: 4px; color: var(--text-muted);">
                      Target: ₹{{ kv.value.entry }} | Current LTP: ₹{{ kv.value.ltp }}
                   </div>
                </div>
              </div>
            </div>

            <div class="glass-card">
               <h3>Manual Entry</h3>
               <form (ngSubmit)="submitManualTrade()" class="manual-form mt-20" style="display: flex; flex-direction: column; gap: 12px;">
                  <div style="display: flex; gap: 8px;">
                    <input type="number" [(ngModel)]="manualTrade.strike" name="strike" placeholder="Strike Price" style="flex: 1;">
                    <select [(ngModel)]="manualTrade.optionType" name="opttype" style="width: 80px;">
                      <option value="CE">CE</option>
                      <option value="PE">PE</option>
                    </select>
                  </div>
                  <input type="number" [(ngModel)]="manualTrade.entryPrice" name="entry" placeholder="Entry Price">
                  <input type="number" [(ngModel)]="manualTrade.qty" name="qty" placeholder="Quantity (Lots)">
                  <button type="submit" class="btn-secondary">EXECUTE ORDER</button>
               </form>
            </div>
          </div>
        </div>

        <!-- OPTION CHAIN VIEW -->
        <div *ngIf="currentView === 'OPTION_CHAIN'">
          <div class="glass-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
              <h3>Live Option Chain (Dhan Gateway)</h3>
              <span class="text-muted" style="font-size: 0.8rem;">OI Data Refreshes every 3s</span>
            </div>
            
            <div style="max-height: 70vh; overflow-y: auto;">
              <table class="oc-table">
                <thead>
                  <tr style="background: rgba(255,255,255,0.02);">
                    <th colspan="2" style="color: #10b981;">CALLS (CE)</th>
                    <th style="background: #1e293b;">STRIKE</th>
                    <th colspan="2" style="color: #f43f5e;">PUTS (PE)</th>
                  </tr>
                  <tr>
                    <th>Vol</th><th>LTP</th>
                    <th>Price</th>
                    <th>LTP</th><th>Vol</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let row of getGroupedOptionChain()" [class.itm-row]="isITM(row.strike)">
                    <td style="text-align: right; color: var(--text-muted);">{{ row.ce?.volume || 0 }}</td>
                    <td style="text-align: right; color: #10b981; font-weight: 600;">₹{{ row.ce?.ltp || 0 }}</td>
                    <td class="strike-cell">₹{{ row.strike }}</td>
                    <td style="text-align: left; color: #f43f5e; font-weight: 600;">₹{{ row.pe?.ltp || 0 }}</td>
                    <td style="text-align: left; color: var(--text-muted);">{{ row.pe?.volume || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- LEDGER VIEW -->
        <div *ngIf="currentView === 'LEDGER'">
           <div class="glass-card">
              <h3>Trade Ledger</h3>
              <div style="overflow-x: auto; margin-top: 20px;">
                <table class="modern-table">
                  <thead>
                    <tr><th>Time</th><th>Details</th><th>Side</th><th>Entry</th><th>Exit</th><th>PnL</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                     <tr *ngFor="let t of trades">
                        <td>{{ t.createdAt | date:'HH:mm:ss' }}</td>
                        <td>{{ t.symbol }} {{ t.strike }}</td>
                        <td>{{ t.optionType }}</td>
                        <td>₹{{ t.entryPrice }}</td>
                        <td>{{ t.exitPrice ? '₹'+t.exitPrice : '-' }}</td>
                        <td [class.neon-green]="t.pnl > 0" [class.neon-red]="t.pnl < 0">
                           {{ t.pnl ? '₹'+t.pnl : '-' }}
                        </td>
                        <td>{{ t.status }}</td>
                     </tr>
                  </tbody>
                </table>
              </div>
           </div>
        </div>

        <!-- BACKTEST VIEW -->
        <div *ngIf="currentView === 'BACKTEST'">
            <div class="glass-card">
              <h3>🧪 Strategy Backtest Lab</h3>
              <div style="display: flex; gap: 16px; align-items: flex-end; margin-top: 20px;">
                <div style="display: flex; flex-direction: column; gap: 4px;">
                   <small class="text-muted">From Date</small>
                   <input type="text" [(ngModel)]="backtestReq.fromDate" placeholder="YYYY-MM-DD">
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px;">
                   <small class="text-muted">To Date</small>
                   <input type="text" [(ngModel)]="backtestReq.toDate" placeholder="YYYY-MM-DD">
                </div>
                <button (click)="runBacktest()" class="btn-secondary" [disabled]="isBacktesting">
                  {{ isBacktesting ? 'SIMULATING...' : 'RUN SIMULATION' }}
                </button>
              </div>
              
              <div *ngIf="backtestResults" class="mt-40">
                 <div class="kpi-grid">
                    <div class="glass-card kpi-card">
                       <small class="text-muted">Simulation Win Rate</small>
                       <div class="kpi-value neon-blue">{{ backtestResults.metrics?.win_rate }}</div>
                    </div>
                    <div class="glass-card kpi-card">
                       <small class="text-muted">Simulation PnL</small>
                       <div class="kpi-value neon-green">₹{{ backtestResults.metrics?.total_pnl }}</div>
                    </div>
                 </div>
                 
                 <table class="modern-table">
                   <thead>
                     <tr><th>Time</th><th>Strike</th><th>Side</th><th>Entry</th><th>Exit</th><th>Result</th><th>PnL</th></tr>
                   </thead>
                   <tbody>
                     <tr *ngFor="let bt of backtestResults.trades">
                        <td>{{ bt.entry_time | slice:11:19 }}</td>
                        <td>{{ bt.strike }}</td>
                        <td>{{ bt.optionType }}</td>
                        <td>₹{{ bt.entry }}</td>
                        <td>₹{{ bt.exit_price || '-' }}</td>
                        <td>{{ bt.result }}</td>
                        <td [class.neon-green]="bt.pnl > 0" [class.neon-red]="bt.pnl < 0">₹{{ bt.pnl | number:'1.1-1' }}</td>
                     </tr>
                   </tbody>
                 </table>
              </div>
            </div>
        </div>

      </section>

      <!-- FOOTER -->
      <footer class="footer">
        <div class="footer-left">
          LuminaQuant v2.0.1 Stable | Exchange: {{ instruments[selectedInstrument]?.segment || 'IDX_I' }}
        </div>
        <div class="footer-right">
          Security: {{ instruments[selectedInstrument]?.id || '-' }} | Current View: {{ currentView }}
        </div>
      </footer>
    </main>
  </div>
  `
})
export class DashboardComponent implements OnInit, OnDestroy {
  currentView: 'TERMINAL' | 'OPTION_CHAIN' | 'LEDGER' | 'BACKTEST' = 'TERMINAL';
  
  // Trading Data
  trades: any[] = [];
  winRate = 0;
  totalPnL = 0;
  activeTradesCount = 0;
  maxDailyLoss = 5000;
  maxTradesPerDay = 10;
  
  // Safety Data
  indiaVix = 15.0;
  vixThreshold = 25.0;
  isNewsPending = false;
  
  // Market Selection
  instruments: any = {};
  expiries: string[] = [];
  selectedInstrument: string = 'NIFTY';
  selectedExpiry: string = '';
  loadingExpiries: boolean = false;

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
    qty: 50
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
  private baseUrl = `${window.location.protocol}//${window.location.hostname}:8080/api`;

  constructor(private http: HttpClient, private auth: AuthService, public router: Router) {}

  onLogout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  ngOnInit() {
    this.fetchInstruments();
    this.fetchProfile();
    this.refreshData();
    this.sub = interval(3000).subscribe(() => this.refreshData());
  }

  fetchProfile() {
    this.http.get<any>(`${this.baseUrl}/user/profile`).subscribe({
      next: (res) => {
        this.maxDailyLoss = res.maxDailyLoss || 5000;
        this.maxTradesPerDay = res.maxTradesPerDay || 10;
        this.vixThreshold = res.vixThreshold || 25.0;
      }
    });
  }

  fetchInstruments() {
    this.http.get<any>(`${this.baseUrl}/user/instruments`).subscribe({
      next: (res) => {
        this.instruments = res.data || {};
        this.onInstrumentChange(this.selectedInstrument);
      }
    });
  }

  getInstrumentList() {
    return Object.keys(this.instruments);
  }

  onInstrumentChange(symbol: string) {
    const inst = this.instruments[symbol];
    if (!inst) return;

    this.loadingExpiries = true;
    this.expiries = [];
    this.selectedExpiry = "";

    this.http.post<any>(`${this.baseUrl}/user/fetch-expiries`, {
      securityId: inst.id,
      segment: inst.segment
    }).subscribe({
      next: (res) => {
        this.loadingExpiries = false;
        this.expiries = res.data || [];
        if (this.expiries.length > 0) {
          this.selectedExpiry = this.expiries[0];
        }
      },
      error: () => {
        this.loadingExpiries = false;
      }
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  refreshData() {
    this.http.get<any[]>(`${this.baseUrl}/trades`).subscribe({
      next: (res) => {
        this.trades = res.reverse();
        this.calculateMetrics();
      },
      error: () => {}
    });

    this.http.get<any>(`${this.baseUrl}/user/engine/status`).subscribe({
      next: (res) => {
        this.autoRunning = res.auto_running;
        this.strategyState = res.strategy_state || {};
      },
      error: () => {}
    });

    this.http.get<any>(`${this.baseUrl}/safety/status`).subscribe({
      next: (res) => {
        this.indiaVix = res.indiaVix;
        this.isNewsPending = res.isNewsPending;
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
    }
  }

  toggleEngine() {
    const inst = this.instruments[this.selectedInstrument];
    const payload = {
      active: !this.autoRunning,
      symbol: this.selectedInstrument,
      securityId: inst?.id?.toString() || "13",
      segment: inst?.segment || "IDX_I",
      expiry: this.selectedExpiry
    };

    this.http.post(`${this.baseUrl}/user/engine/toggle`, payload).subscribe({
      next: () => {
        this.autoRunning = !this.autoRunning;
      }
    });
  }

  getTrackedStrikes() {
    return Object.keys(this.strategyState).filter(k => k !== 'option_chain').map(key => ({
      key,
      value: this.strategyState[key]
    }));
  }

  getGroupedOptionChain() {
    const chain = this.strategyState['option_chain'] || [];
    const grouped: any = {};
    chain.forEach((opt: any) => {
      if (!grouped[opt.strikePrice]) {
        grouped[opt.strikePrice] = { strike: opt.strikePrice };
      }
      if (opt.optionType === 'CE') {
        grouped[opt.strikePrice].ce = opt;
      } else {
        grouped[opt.strikePrice].pe = opt;
      }
    });
    return Object.values(grouped).sort((a: any, b: any) => b.strike - a.strike);
  }

  isITM(strike: number): boolean {
    return Math.abs(strike - 24500) < 100;
  }

  submitManualTrade() {
    if (!this.manualTrade.strike || !this.manualTrade.entryPrice) return;
    this.isSubmitting = true;
    
    const payload = {
        symbol: this.selectedInstrument,
        strike: this.manualTrade.strike,
        optionType: this.manualTrade.optionType,
        entryPrice: this.manualTrade.entryPrice,
        qty: this.manualTrade.qty,
        strategyName: "Manual"
    };

    this.http.post(`${this.baseUrl}/trade`, payload).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.manualTrade.strike = null;
        this.manualTrade.entryPrice = null;
        alert("Order placed successfully.");
      },
      error: () => {
        this.isSubmitting = false;
        alert("Failed to execute trade.");
      }
    });
  }

  runBacktest() {
    if (!this.backtestReq.fromDate || !this.backtestReq.toDate) return;
    this.isBacktesting = true;
    this.backtestError = null;
    this.backtestResults = null;
    
    this.http.post<any>(`${this.baseUrl}/backtest/run`, this.backtestReq).subscribe({
      next: (res) => {
        this.isBacktesting = false;
        if (res.error) {
          this.backtestError = res.error;
        } else {
          this.backtestResults = res;
        }
      },
      error: () => {
        this.isBacktesting = false;
        this.backtestError = "Failed to reach backtest engine.";
      }
    });
  }
}
