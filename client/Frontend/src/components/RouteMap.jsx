export default function RouteMap() {
  return (
    <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden glass">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Live Route Map — A3 Highway</span>
        <span className="text-xs text-text3 font-mono">GPS · 30s interval</span>
      </div>
      <div className="p-4">
        <svg className="w-full h-auto" viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg">
          {/* Background */}
          <rect width="680" height="300" fill="#0a0b0f" rx="8"/>

          {/* Grid lines faint */}
          <line x1="0" y1="100" x2="680" y2="100" stroke="#1a1d23" strokeWidth="1"/>
          <line x1="0" y1="200" x2="680" y2="200" stroke="#1a1d23" strokeWidth="1"/>
          <line x1="170" y1="0" x2="170" y2="300" stroke="#1a1d23" strokeWidth="1"/>
          <line x1="340" y1="0" x2="340" y2="300" stroke="#1a1d23" strokeWidth="1"/>
          <line x1="510" y1="0" x2="510" y2="300" stroke="#1a1d23" strokeWidth="1"/>

          {/* Terrain suggestions */}
          <ellipse cx="420" cy="80" rx="90" ry="30" fill="rgba(6, 182, 212, 0.04)"/>
          <ellipse cx="500" cy="160" rx="70" ry="40" fill="rgba(6, 182, 212, 0.05)"/>
          <text x="420" y="58" textAnchor="middle" fontSize="9" fill="#06b6d4" fontFamily="'JetBrains Mono',monospace" letterSpacing="0.08em">HIGHLANDS</text>

          {/* Road shadow */}
          <path d="M60,160 Q160,100 290,120 Q390,140 490,100 Q560,80 620,110" stroke="#1a1d23" strokeWidth="22" fill="none" strokeLinecap="round"/>
          {/* Road surface */}
          <path d="M60,160 Q160,100 290,120 Q390,140 490,100 Q560,80 620,110" stroke="#2d333b" strokeWidth="16" fill="none" strokeLinecap="round"/>
          {/* Center line */}
          <path d="M60,160 Q160,100 290,120 Q390,140 490,100 Q560,80 620,110" stroke="#64748b" strokeWidth="1" fill="none" strokeDasharray="14 10" strokeLinecap="round"/>

          {/* Checkpoints */}
          {/* Harare */}
          <circle cx="60" cy="160" r="12" fill="#0a0b0f" stroke="#10b981" strokeWidth="2"/>
          <circle cx="60" cy="160" r="6" fill="#10b981"/>
          <text x="60" y="182" textAnchor="middle" fontSize="11" fill="#10b981" fontFamily="'JetBrains Mono',monospace" fontWeight="600">Harare</text>
          <text x="60" y="194" textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace">0 km</text>

          {/* Marondera */}
          <circle cx="185" cy="110" r="8" fill="#0a0b0f" stroke="#10b981" strokeWidth="1.5"/>
          <circle cx="185" cy="110" r="4" fill="#10b981"/>
          <text x="185" y="98" textAnchor="middle" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Marondera</text>
          <text x="185" y="87" textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace">72 km</text>

          {/* Macheke */}
          <circle cx="290" cy="119" r="8" fill="#0a0b0f" stroke="#10b981" strokeWidth="1.5"/>
          <circle cx="290" cy="119" r="4" fill="#10b981"/>
          <text x="290" y="107" textAnchor="middle" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Macheke</text>
          <text x="290" y="96" textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace">120 km</text>

          {/* Rusape */}
          <circle cx="400" cy="128" r="8" fill="#0a0b0f" stroke="#10b981" strokeWidth="1.5"/>
          <circle cx="400" cy="128" r="4" fill="#10b981"/>
          <text x="400" y="148" textAnchor="middle" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Rusape</text>
          <text x="400" y="159" textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace">160 km</text>

          {/* Headlands */}
          <circle cx="500" cy="100" r="8" fill="#0a0b0f" stroke="#3b82f6" strokeWidth="1.5"/>
          <circle cx="500" cy="100" r="4" fill="#3b82f6"/>
          <circle cx="500" cy="100" r="11" fill="none" stroke="rgba(59, 130, 246, 0.3)" strokeWidth="1">
            <animate attributeName="r" from="8" to="16" dur="2s" repeatCount="indefinite"/>
            <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite"/>
          </circle>
          <text x="500" y="88" textAnchor="middle" fontSize="10" fill="#3b82f6" fontFamily="'JetBrains Mono',monospace">Headlands</text>
          <text x="500" y="77" textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace">199 km</text>

          {/* Mutare */}
          <circle cx="620" cy="110" r="12" fill="#0a0b0f" stroke="#64748b" strokeWidth="2"/>
          <circle cx="620" cy="110" r="6" fill="#2d333b"/>
          <text x="620" y="132" textAnchor="middle" fontSize="11" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace" fontWeight="600">Mutare</text>
          <text x="620" y="144" textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace">263 km</text>

          {/* TRUCKS */}
          {/* T1 at Headlands (moving) */}
          <g transform="translate(500,100)">
            <rect x="-18" y="-11" width="36" height="22" rx="5" fill="#3b82f6"/>
            <rect x="14" y="-7" width="10" height="14" rx="3" fill="#60a5fa"/>
            <circle cx="-10" cy="11" r="5" fill="#0a0b0f"/>
            <circle cx="10" cy="11" r="5" fill="#0a0b0f"/>
            <text x="-1" y="-16" textAnchor="middle" fontSize="9" fill="#3b82f6" fontFamily="'JetBrains Mono',monospace" fontWeight="500">T1</text>
          </g>

          {/* T2 at Macheke (delayed) */}
          <g transform="translate(290,119)">
            <rect x="-18" y="-11" width="36" height="22" rx="5" fill="#f59e0b"/>
            <rect x="14" y="-7" width="10" height="14" rx="3" fill="#fbbf24"/>
            <circle cx="-10" cy="11" r="5" fill="#0a0b0f"/>
            <circle cx="10" cy="11" r="5" fill="#0a0b0f"/>
            <text x="-1" y="-16" textAnchor="middle" fontSize="9" fill="#f59e0b" fontFamily="'JetBrains Mono',monospace" fontWeight="500">T2</text>
          </g>

          {/* T3 at Marondera (stopped) */}
          <g transform="translate(185,110)">
            <rect x="-18" y="-11" width="36" height="22" rx="5" fill="#ef4444"/>
            <rect x="14" y="-7" width="10" height="14" rx="3" fill="#f87171"/>
            <circle cx="-10" cy="11" r="5" fill="#0a0b0f"/>
            <circle cx="10" cy="11" r="5" fill="#0a0b0f"/>
            <text x="-1" y="-16" textAnchor="middle" fontSize="9" fill="#ef4444" fontFamily="'JetBrains Mono',monospace" fontWeight="500">T3</text>
          </g>

          {/* T4 at Rusape (moving) */}
          <g transform="translate(400,128)">
            <rect x="-18" y="-11" width="36" height="22" rx="5" fill="#10b981"/>
            <rect x="14" y="-7" width="10" height="14" rx="3" fill="#34d399"/>
            <circle cx="-10" cy="11" r="5" fill="#0a0b0f"/>
            <circle cx="10" cy="11" r="5" fill="#0a0b0f"/>
            <text x="-1" y="-16" textAnchor="middle" fontSize="9" fill="#10b981" fontFamily="'JetBrains Mono',monospace" fontWeight="500">T4</text>
          </g>

          {/* T5 at Headlands (moving) */}
          <g transform="translate(513,82)">
            <rect x="-18" y="-11" width="36" height="22" rx="5" fill="#3b82f6"/>
            <rect x="14" y="-7" width="10" height="14" rx="3" fill="#60a5fa"/>
            <circle cx="-10" cy="11" r="5" fill="#0a0b0f"/>
            <circle cx="10" cy="11" r="5" fill="#0a0b0f"/>
            <text x="-1" y="-16" textAnchor="middle" fontSize="9" fill="#3b82f6" fontFamily="'JetBrains Mono',monospace" fontWeight="500">T5</text>
          </g>

          {/* T6 delivered at Mutare */}
          <g transform="translate(620,110)">
            <rect x="-18" y="-11" width="36" height="22" rx="5" fill="#64748b"/>
            <rect x="14" y="-7" width="10" height="14" rx="3" fill="#94a3b8"/>
            <circle cx="-10" cy="11" r="5" fill="#0a0b0f"/>
            <circle cx="10" cy="11" r="5" fill="#0a0b0f"/>
            <text x="-1" y="-16" textAnchor="middle" fontSize="9" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace" fontWeight="500">T6</text>
          </g>

          {/* LEGEND */}
          <rect x="14" y="220" width="180" height="68" rx="6" fill="#111218" stroke="#1a1d23" strokeWidth="1"/>
          <text x="24" y="236" fontSize="9" fill="#64748b" fontFamily="'JetBrains Mono',monospace" fontWeight="600" letterSpacing="0.07em">LEGEND</text>
          <rect x="24" y="242" width="10" height="6" rx="2" fill="#3b82f6"/>
          <text x="38" y="249" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Moving</text>
          <rect x="24" y="254" width="10" height="6" rx="2" fill="#f59e0b"/>
          <text x="38" y="261" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Delayed</text>
          <rect x="24" y="266" width="10" height="6" rx="2" fill="#ef4444"/>
          <text x="38" y="273" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Stopped</text>
          <rect x="100" y="242" width="10" height="6" rx="2" fill="#10b981"/>
          <text x="114" y="249" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">On Schedule</text>
          <circle cx="105" cy="259" r="4" fill="#3b82f6" opacity="0.6"/>
          <text x="114" y="262" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Active CP</text>
          <rect x="100" y="266" width="10" height="6" rx="2" fill="#64748b"/>
          <text x="114" y="273" fontSize="10" fill="#94a3b8" fontFamily="'JetBrains Mono',monospace">Delivered</text>
        </svg>
      </div>
    </div>
  );
}
