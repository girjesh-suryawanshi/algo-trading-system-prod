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

          <div class="mode-toggle">
            <span class="toggle-label paper" [class.active]="paperTradingMode">Paper</span>
            <label class="switch">
              <input type="checkbox" [checked]="!paperTradingMode" (change)="toggleTradingMode()">
              <span class="slider"></span>
            </label>
            <span class="toggle-label live" [class.active]="!paperTradingMode">Live</span>
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
            <div class="glass-card kpi-card neon-border">
              <small class="text-muted">Virtual Balance</small>
              <div class="kpi-value neon-purple">₹{{ virtualBalance | number:'1.2-2' }}</div>
            </div>
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

          <div class="glass-card mt-20">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
              <h3>Active Tracking</h3>
              <div *ngIf="autoRunning" class="pulse-text" style="color: #10b981; font-size: 0.8rem;">● Engine Scanning Markets</div>
            </div>
            
            <div class="tracker-table-container">
              <table class="modern-table">
                <thead>
                  <tr>
                    <th>Instrument</th>
                    <th>Strike</th>
                    <th>Expiry</th>
                    <th>OI</th>
                    <th>LTP</th>
                    <th>7D Low</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngIf="getTrackedStrikes().length === 0">
                    <td colspan="8" class="empty-state">Engine is searching for entries based on your strategy...</td>
                  </tr>
                  <tr *ngFor="let kv of getTrackedStrikes()">
                    <td>{{ kv.value.symbol || 'NIFTY' }}</td>
                    <td><span class="badge" [class.ce]="kv.value.optionType === 'CE'" [class.pe]="kv.value.optionType === 'PE'">{{ kv.value.strike }} {{ kv.value.optionType }}</span></td>
                    <td>{{ kv.value.expiry || '-' }}</td>
                    <td>{{ kv.value.oi | number }}</td>
                    <td class="neon-blue">₹{{ kv.value.ltp }}</td>
                    <td class="text-muted">₹{{ kv.value.low }}</td>
                    <td>
                      <span class="status-pill" [attr.data-status]="kv.value.status">{{ kv.value.status }}</span>
                    </td>
                    <td>
                      <button class="btn-action" (click)="openOrderModal(kv.value)">Execute Trade</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="glass-card mt-20">
            <h3>Live working orders</h3>
            <div class="tracker-table-container mt-15">
              <table class="modern-table">
                <thead>
                  <tr><th>Time</th><th>Details</th><th>Side</th><th>Entry</th><th>Status</th></tr>
                </thead>
                <tbody>
                  <tr *ngIf="getWorkingOrders().length === 0">
                    <td colspan="5" class="empty-state">No active working orders found.</td>
                  </tr>
                  <tr *ngFor="let t of getWorkingOrders()">
                    <td>{{ t.createdAt | date:'HH:mm:ss' }}</td>
                    <td>{{ t.symbol }} {{ t.strike }}</td>
                    <td>{{ t.optionType }}</td>
                    <td>₹{{ t.entryPrice }}</td>
                    <td><span class="status-pill" data-status="OPEN">{{ t.status }}</span></td>
                  </tr>
                </tbody>
              </table>
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

        <div *ngIf="currentView === 'BACKTEST'" class="glass-card backtest-lab">
              <div class="lab-header">
                <h3>🧪 Strategy Backtest Lab</h3>
                <p class="text-muted">High-fidelity simulation using Dhan Rolling Options API</p>
              </div>

              <div class="lab-controls">
                <div class="control-group">
                   <label>Instrument</label>
                   <div class="neon-select-wrapper">
                     <select [(ngModel)]="backtestReq.symbol" (change)="onBacktestInstrumentChange()" [disabled]="isBacktesting">
                        <option value="NIFTY">NIFTY 50</option>
                        <option value="BANKNIFTY">BANK NIFTY</option>
                        <option value="FINNIFTY">FIN NIFTY</option>
                     </select>
                   </div>
                </div>
                
                <div class="control-group">
                   <label>Expiry Cycle</label>
                   <div class="neon-select-wrapper">
                     <select [(ngModel)]="backtestReq.expiryFlag" [disabled]="isBacktesting">
                        <option value="WEEK">WEEKLY</option>
                        <option value="MONTH">MONTHLY</option>
                     </select>
                   </div>
                </div>

                <div class="control-group">
                   <label>From Date</label>
                   <input type="date" [(ngModel)]="backtestReq.fromDate" [disabled]="isBacktesting" class="neon-input">
                </div>

                <div class="control-group">
                   <label>To Date</label>
                   <input type="date" [(ngModel)]="backtestReq.toDate" [disabled]="isBacktesting" class="neon-input">
                </div>

                <button (click)="runBacktest()" class="btn-launch" [disabled]="isBacktesting">
                  <span class="btn-text">{{ isBacktesting ? 'SIMULATING...' : 'RUN SIMULATION' }}</span>
                  <span class="btn-icon" *ngIf="!isBacktesting">🚀</span>
                </button>
              </div>

              <!-- PROGRESS SECTION -->
              <div *ngIf="isBacktesting" class="progress-section animate-fade-in">
                <div class="progress-info">
                  <span class="status-text">{{ backtestStatus }}</span>
                  <span class="percentage">{{ backtestProgress }}%</span>
                </div>
                <div class="progress-bar-container">
                  <div class="progress-bar-fill" [style.width.%]="backtestProgress">
                    <div class="progress-glow"></div>
                  </div>
                </div>
              </div>

              
              <div *ngIf="backtestError" class="glass-card mt-20 animate-pop" style="border-color: rgba(255, 68, 68, 0.4); background: rgba(255, 68, 68, 0.05);">
                  <div style="color: #ff4444; font-weight: 500;">🛑 Backtest Error</div>
                  <div class="text-muted small mt-4">{{ backtestError }}</div>
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
                      <tr>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Strike</th>
                        <th>Side</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>Result</th>
                        <th>PnL</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let bt of backtestResults.trades" class="animate-fade-in">
                         <td class="text-accent">{{ bt.entry_time | slice:0:10 }}</td>
                         <td>{{ bt.entry_time | slice:11:16 }}</td>
                         <td><span class="badge-strike">{{ bt.strike }}</span></td>
                         <td><span class="badge" [class.ce]="bt.optionType === 'CE'" [class.pe]="bt.optionType === 'PE'">{{ bt.optionType }}</span></td>
                         <td class="neon-blue">₹{{ bt.entry }}</td>
                         <td>₹{{ bt.exit_price || '-' }}</td>
                         <td>
                           <span class="status-pill" [attr.data-status]="bt.result">{{ bt.result }}</span>
                         </td>
                         <td [class.neon-green]="bt.pnl > 0" [class.neon-red]="bt.pnl < 0" style="font-weight: 800;">
                           ₹{{ bt.pnl | number:'1.1-1' }}
                         </td>
                      </tr>
                    </tbody>
                  </table>
              </div>
        </div>

      </section>

      <!-- ORDER MODAL -->
      <div class="modal-overlay" *ngIf="showOrderModal">
        <div class="glass-card modal-content animate-pop">
           <div class="modal-header">
              <h3>Manual Trade Execution</h3>
              <button class="btn-close" (click)="closeOrderModal()">×</button>
           </div>
           
           <div class="modal-body">
              <div class="preview-banner">
                 <strong>{{ manualTrade.symbol }} {{ manualTrade.strike }} {{ manualTrade.optionType }}</strong>
                 <span>LTP: ₹{{ selectedTrackItem?.ltp }}</span>
              </div>

              <form (ngSubmit)="submitManualTrade()" class="manual-form mt-20">
                 <div class="form-grid">
                    <div class="form-group">
                       <label>Entry Price</label>
                       <input type="number" [(ngModel)]="manualTrade.entryPrice" name="entry" placeholder="0.00">
                    </div>
                    <div class="form-group">
                       <label>Quantity (Lots)</label>
                       <input type="number" [(ngModel)]="manualTrade.qty" name="qty" placeholder="50">
                    </div>
                    <div class="form-group">
                       <label>Stop Loss (₹)</label>
                       <input type="number" [(ngModel)]="manualTrade.stopLoss" name="sl" placeholder="0.00">
                    </div>
                    <div class="form-group">
                       <label>Target (₹)</label>
                       <input type="number" [(ngModel)]="manualTrade.target1" name="target" placeholder="0.00">
                    </div>
                    <div class="form-group full-width">
                       <label>Trailing SL (%)</label>
                       <input type="number" [(ngModel)]="manualTrade.tslPercentage" name="tsl" placeholder="e.g. 2">
                    </div>
                 </div>
                 
                 <div class="modal-actions mt-20">
                    <button type="button" class="btn-secondary outline" (click)="closeOrderModal()">CANCEL</button>
                    <button type="submit" class="btn-secondary" [disabled]="isSubmitting">
                       {{ isSubmitting ? 'PLACING ORDER...' : 'CONFIRM & EXECUTE' }}
                    </button>
                 </div>
              </form>
           </div>
        </div>
      </div>

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
  virtualBalance = 1000000.0;
  
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
  paperTradingMode = true;
  strategyState: any = {};
  
  // Manual Form & Modal State
  showOrderModal = false;
  selectedTrackItem: any = null;
  isSubmitting = false;
  manualTrade = {
    symbol: 'NIFTY',
    optionType: 'CE',
    strike: null as number | null,
    entryPrice: null as number | null,
    qty: 50,
    stopLoss: null as number | null,
    target1: null as number | null,
    tslPercentage: 2.0
  };
  
  // Backtest Module State
  isBacktesting = false;
  backtestResults: any = null;
  backtestError: string | null = null;
  backtestStatus: string = '';
  backtestProgress: number = 0;
  backtestReq = {
    symbol: 'NIFTY',
    securityId: '13',
    segment: 'NSE_FNO',
    expiryFlag: 'WEEK',
    fromDate: '2026-03-24',
    toDate: '2026-03-27'
  };

  onBacktestInstrumentChange() {
    const symbol = this.backtestReq.symbol;
    if (symbol === 'NIFTY') {
      this.backtestReq.securityId = '13';
      this.backtestReq.segment = 'NSE_FNO';
    } else if (symbol === 'BANKNIFTY') {
      this.backtestReq.securityId = '25';
      this.backtestReq.segment = 'NSE_FNO';
    } else if (symbol === 'FINNIFTY') {
      this.backtestReq.securityId = '27';
      this.backtestReq.segment = 'NSE_FNO';
    }
  }

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
        this.virtualBalance = res.virtualBalance || 1000000.0;
        this.paperTradingMode = res.paperTradingMode !== undefined ? res.paperTradingMode : true;
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
    this.fetchProfile();

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
        // Prioritize Real-time VIX from Python Engine
        if (this.strategyState.indiaVix) {
          this.indiaVix = this.strategyState.indiaVix;
        }
      },
      error: () => {}
    });

    this.http.get<any>(`${this.baseUrl}/safety/status`).subscribe({
      next: (res) => {
        // Only use backend VIX if engine VIX is not available
        if (!this.strategyState.indiaVix) {
          this.indiaVix = res.indiaVix;
        }
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

  toggleTradingMode() {
    const newMode = !this.paperTradingMode;
    this.http.put(`${this.baseUrl}/user/profile`, { paperTradingMode: newMode }).subscribe({
      next: () => {
        this.paperTradingMode = newMode;
        // Optional: Show toast
      },
      error: () => {
        alert("Failed to switch trading mode.");
      }
    });
  }

  getTrackedStrikes() {
    const pendingSignals = this.strategyState['PENDING_SIGNALS'] || {};
    const chain = this.strategyState['option_chain'] || [];
    
    return Object.keys(pendingSignals).map(key => {
      const item = { ...pendingSignals[key] };
      // Fallback: If LTP is 0, try to fetch from Option Chain state
      if (item.ltp === 0) {
        const match = chain.find((c: any) => 
          c.strikePrice === item.strike && 
          c.optionType === item.optionType
        );
        if (match && match.ltp > 0) {
          item.ltp = match.ltp;
        }
      }
      return { key, value: item };
    });
  }

  getWorkingOrders() {
    return this.trades.filter(t => t.status === 'OPEN' || t.status === 'WAITING');
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
    const spot = this.selectedInstrument === 'NIFTY' ? 24500 : 52000; // Mock spot
    return Math.abs(strike - spot) < 100;
  }

  openOrderModal(item: any) {
    this.selectedTrackItem = item;
    this.manualTrade.strike = item.strike;
    this.manualTrade.optionType = item.optionType;
    this.manualTrade.entryPrice = item.entryPrice || item.ltp;
    this.manualTrade.stopLoss = item.stopLoss || Math.round(this.manualTrade.entryPrice! * 0.9);
    this.manualTrade.target1 = item.target1 || Math.round(this.manualTrade.entryPrice! * 1.1);
    this.showOrderModal = true;
  }

  closeOrderModal() {
    this.showOrderModal = false;
    this.selectedTrackItem = null;
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
        stopLoss: this.manualTrade.stopLoss,
        target1: this.manualTrade.target1,
        tslPercentage: this.manualTrade.tslPercentage,
        strategyName: "Manual",
        manualTrade: true
    };

    this.http.post(`${this.baseUrl}/trade`, payload).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.closeOrderModal();
        this.refreshData();
      },
      error: (err) => {
        this.isSubmitting = false;
        const msg = err.error || "Failed to execute trade.";
        alert(msg);
      }
    });
  }

  runBacktest() {
    if (!this.backtestReq.fromDate || !this.backtestReq.toDate) return;
    this.isBacktesting = true;
    this.backtestError = null;
    this.backtestResults = null;
    this.backtestStatus = 'Connecting to Dhan Rolling API...';
    this.backtestProgress = 5;
    
    // Animate progress (Phase 1 & 2)
    const statusInterval = setInterval(() => {
        if (!this.isBacktesting) {
            clearInterval(statusInterval);
            return;
        }
        
        if (this.backtestProgress < 90) {
          this.backtestProgress += Math.floor(Math.random() * 5) + 1;
        }

        if (this.backtestProgress < 30) {
            this.backtestStatus = 'Phase 1/3: Scoping Historical Floors (Sniper Logic)...';
        } else if (this.backtestProgress < 70) {
            this.backtestStatus = 'Phase 2/3: Fetching 1-Min Intraday Rolling Data...';
        } else {
            this.backtestStatus = 'Phase 3/3: Simulating Two-Stage Sniper Execution...';
        }
    }, 1500);

    this.http.post<any>(`${this.baseUrl}/backtest/run`, this.backtestReq).subscribe({
      next: (res) => {
        this.isBacktesting = false;
        this.backtestProgress = 100;
        this.backtestStatus = 'Simulation Complete';
        clearInterval(statusInterval);
        if (res.error) {
          this.backtestError = res.error;
        } else if (!res.trades || res.trades.length === 0) {
          this.backtestError = "Zero Trades Found: No entry conditions (Low x 2) were met for this period.";
        } else {
          this.backtestResults = res;
        }
      },
      error: (err) => {
        this.isBacktesting = false;
        this.backtestProgress = 0;
        this.backtestStatus = '';
        clearInterval(statusInterval);
        this.backtestError = err.error?.error || "Connection Timeout: Server is taking too long to process high-fidelity data.";
      }
    });
  }
}
