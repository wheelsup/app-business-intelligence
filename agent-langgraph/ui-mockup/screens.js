// Screens 2, 3, 4 injected after page load
document.addEventListener('DOMContentLoaded', () => {
  document.body.insertAdjacentHTML('beforeend', `

<!-- SCREEN 2: ACTIVE CHAT -->
<div id="screen-chat" class="screen">
<div class="shell">
  <aside class="sb">
    <div class="sbh">
      <svg class="wumark" viewBox="0 0 116 20" xmlns="http://www.w3.org/2000/svg"><text x="0" y="17" font-family="'Arial Black',Arial,sans-serif" font-weight="900" font-style="italic" font-size="17" fill="#FFFFFF" letter-spacing="0.5">WHEELS UP</text></svg>
      <button class="colbtn" onclick="toggleSidebar(this)" title="Collapse sidebar"><span class="material-symbols-rounded">left_panel_close</span></button>
    </div>
    <div class="sbnav"><button class="sbbtn"><span class="material-symbols-rounded">add_comment</span><span>New chat</span></button></div>
    <div class="sbsec">Recent</div>
    <div class="sbhist">
      <div class="hi act"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Top routes by revenue YTD</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">On-time performance May 2025</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Fleet utilization by aircraft type</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Member cancellation trends Q1</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Revenue by booking method</span></div>
    </div>
    <div class="sbfoot"><div class="urow"><div class="av">JD</div><div class="uinfo"><div class="uname">Javier Dela Cruz</div><div class="uemail">javier.delacruz@wheelsup.com</div></div></div></div>
  </aside>
  <div class="main">
    <div class="chdr">
      <div class="chdr-title">Top routes by revenue YTD</div>
      <div class="chdr-acts">
        <button class="ibtn" title="Share"><span class="material-symbols-rounded">ios_share</span></button>
        <button class="ibtn" title="More options"><span class="material-symbols-rounded">more_vert</span></button>
      </div>
    </div>
    <div class="marea">
      <div class="minner">
        <div class="msg">
          <div class="mrole"><div class="ric u">J</div>You</div>
          <div class="mbub u">Show me the top 10 routes by revenue year-to-date, grouped by fleet type.</div>
        </div>
        <div class="msg">
          <div class="mrole"><div class="ric a">W</div>WheelsUp AI</div>
          <div class="tpill done">✓ query_flights_genie — Queried reporting_flight for YTD revenue by route</div>
          <div class="mbub">
            <p>Here are the <strong>top 10 routes by revenue</strong> year-to-date, broken down by fleet type:</p>
            <table class="dtbl">
              <thead><tr><th>#</th><th>Route</th><th>Fleet Type</th><th>Revenue (YTD)</th><th>Flights</th><th>Trend</th></tr></thead>
              <tbody>
                <tr><td>1</td><td>KTEB → KMIA</td><td><span class="bdg sky">Large Cabin</span></td><td>$4.2M</td><td>312</td><td><span class="bdg g">↑ +18%</span></td></tr>
                <tr><td>2</td><td>KLAX → KSFO</td><td><span class="bdg sky">Midsize</span></td><td>$3.8M</td><td>287</td><td><span class="bdg g">↑ +12%</span></td></tr>
                <tr><td>3</td><td>KORD → KTEB</td><td><span class="bdg sky">Large Cabin</span></td><td>$3.5M</td><td>241</td><td><span class="bdg r">↓ -4%</span></td></tr>
                <tr><td>4</td><td>KMIA → KPBI</td><td><span class="bdg sky">Light</span></td><td>$2.9M</td><td>398</td><td><span class="bdg g">↑ +22%</span></td></tr>
                <tr><td>5</td><td>KBOS → KTEB</td><td><span class="bdg sky">Midsize</span></td><td>$2.7M</td><td>209</td><td><span class="bdg g">↑ +8%</span></td></tr>
                <tr><td>6</td><td>KDAL → KHOU</td><td><span class="bdg sky">Light</span></td><td>$2.4M</td><td>356</td><td><span class="bdg g">↑ +5%</span></td></tr>
                <tr><td>7</td><td>KSFO → KLAS</td><td><span class="bdg sky">Midsize</span></td><td>$2.1M</td><td>178</td><td><span class="bdg r">↓ -2%</span></td></tr>
                <tr><td>8</td><td>KLGA → KBOS</td><td><span class="bdg sky">Light</span></td><td>$1.9M</td><td>301</td><td><span class="bdg g">↑ +14%</span></td></tr>
                <tr><td>9</td><td>KDEN → KSLC</td><td><span class="bdg sky">Midsize</span></td><td>$1.7M</td><td>155</td><td><span class="bdg g">↑ +9%</span></td></tr>
                <tr><td>10</td><td>KATL → KMIA</td><td><span class="bdg sky">Large Cabin</span></td><td>$1.6M</td><td>134</td><td><span class="bdg r">↓ -7%</span></td></tr>
              </tbody>
            </table>
            <p style="margin-top:12px;font-size:12px;color:var(--t3)">Total YTD revenue across top 10 routes: <strong style="color:var(--t)">$26.8M</strong> · Data as of May 16, 2025</p>
          </div>
          <div class="macts">
            <button class="abtn"><span class="material-symbols-rounded">content_copy</span>Copy</button>
            <button class="abtn"><span class="material-symbols-rounded">refresh</span>Regenerate</button>
            <button class="abtn"><span class="material-symbols-rounded">thumb_up</span></button>
            <button class="abtn"><span class="material-symbols-rounded">thumb_down</span></button>
          </div>
        </div>
        <div class="msg">
          <div class="mrole"><div class="ric u">J</div>You</div>
          <div class="mbub u">Which of these routes had the highest average revenue per flight?</div>
        </div>
        <div class="msg">
          <div class="mrole"><div class="ric a">W</div>WheelsUp AI</div>
          <div class="tpill done">✓ query_flights_genie — Calculated avg revenue per flight for top routes</div>
          <div class="mbub">
            <p>Based on the data above, <strong>KTEB → KMIA</strong> leads in total revenue, but <strong>KORD → KTEB</strong> has the highest average revenue per flight at <strong>$14,523/flight</strong>, driven by its Large Cabin fleet mix and longer stage length.</p>
            <p>Top 3 by avg revenue per flight:</p>
            <table class="dtbl" style="margin-top:8px">
              <thead><tr><th>Route</th><th>Avg Rev/Flight</th><th>Fleet</th></tr></thead>
              <tbody>
                <tr><td>KORD → KTEB</td><td>$14,523</td><td><span class="bdg sky">Large Cabin</span></td></tr>
                <tr><td>KTEB → KMIA</td><td>$13,462</td><td><span class="bdg sky">Large Cabin</span></td></tr>
                <tr><td>KATL → KMIA</td><td>$11,940</td><td><span class="bdg sky">Large Cabin</span></td></tr>
              </tbody>
            </table>
          </div>
          <div class="macts">
            <button class="abtn"><span class="material-symbols-rounded">content_copy</span>Copy</button>
            <button class="abtn"><span class="material-symbols-rounded">refresh</span>Regenerate</button>
            <button class="abtn"><span class="material-symbols-rounded">thumb_up</span></button>
            <button class="abtn"><span class="material-symbols-rounded">thumb_down</span></button>
          </div>
        </div>
        <!-- Streaming message -->
        <div class="msg">
          <div class="mrole"><div class="ric u">J</div>You</div>
          <div class="mbub u">What context do you have about our fleet policies?</div>
        </div>
        <div class="msg">
          <div class="mrole"><div class="ric a">W</div>WheelsUp AI</div>
          <div class="tpill"><div class="spin"></div>search_flights_context — Searching knowledge base…</div>
          <div class="mbub">
            Based on the knowledge base, WheelsUp operates under a multi-fleet policy that prioritizes member satisfaction and operational efficiency<span class="cur"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="iarea">
      <div class="iwrap">
        <div class="ibox">
          <textarea class="ita" placeholder="Ask a follow-up question…" rows="1"></textarea>
          <button class="sbtn"><span class="material-symbols-rounded">arrow_upward</span></button>
        </div>
        <div class="idisc">WheelsUp AI may make mistakes. Always verify critical data.</div>
      </div>
    </div>
  </div>
</div>
</div>

<!-- SCREEN 3: CHAT STYLE (matches actual app) -->
<div id="screen-appstyle" class="screen">
<div class="shell">
  <aside class="sb">
    <div class="sbh">
      <svg class="wumark" viewBox="0 0 116 20" xmlns="http://www.w3.org/2000/svg"><text x="0" y="17" font-family="Arial Black,Arial,sans-serif" font-weight="900" font-style="italic" font-size="17" fill="#FFFFFF">WHEELS UP</text></svg>
      <button class="colbtn" onclick="toggleSidebar(this)" title="Collapse sidebar"><span class="material-symbols-rounded">left_panel_close</span></button>
    </div>
    <div class="sbnav"><button class="sbbtn"><span class="material-symbols-rounded">add_comment</span><span>New chat</span></button></div>
    <div class="sbsec">Recent</div>
    <div class="sbhist">
      <div class="hi act"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Top routes by revenue YTD</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">On-time performance May 2025</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Fleet utilization by aircraft type</span></div>
    </div>
    <div class="sbfoot"><div class="urow"><div class="av">JD</div><div class="uinfo"><div class="uname">Javier Dela Cruz</div><div class="uemail">javier.delacruz@wheelsup.com</div></div></div></div>
  </aside>
  <div class="main">
    <div class="chdr">
      <div class="chdr-title">Top routes by revenue YTD</div>
    </div>
    <div class="marea">
      <div class="minner2">
        <div class="msg2">
          <div class="mbub2-u">are you there?</div>
        </div>
        <div class="msg2">
          <div class="mbub2-a">
            <p>Yes, I am here! How can I help you today?</p>
            <p>Whether you have questions about <strong>flight data</strong> (like counts, trends, or specific records) or need help looking up <strong>definitions, policies, or glossary terms</strong>, I am ready to assist. Just ask!</p>
          </div>
          <div class="macts2">
            <button class="abtn2" title="Copy"><span class="material-symbols-rounded">content_copy</span></button>
            <button class="abtn2" title="Thumbs up"><span class="material-symbols-rounded">thumb_up</span></button>
            <button class="abtn2" title="Thumbs down"><span class="material-symbols-rounded">thumb_down</span></button>
          </div>
        </div>
        <div class="msg2">
          <div class="mbub2-u">Show me top 5 routes by revenue year-to-date</div>
        </div>
        <div class="msg2">
          <div class="tpill done" style="margin-bottom:10px">&#10003; query_flights_genie &#8212; Queried reporting_flight for YTD revenue by route</div>
          <div class="mbub2-a">
            <p>Here are the <strong>top 5 routes by revenue</strong> year-to-date:</p>
            <table class="dtbl">
              <thead><tr><th>#</th><th>Route</th><th>Fleet</th><th>Revenue YTD</th><th>Trend</th></tr></thead>
              <tbody>
                <tr><td>1</td><td>KTEB &#8594; KMIA</td><td><span class="bdg sky">Large Cabin</span></td><td>$4.2M</td><td><span class="bdg g">&#8593; +18%</span></td></tr>
                <tr><td>2</td><td>KLAX &#8594; KSFO</td><td><span class="bdg sky">Midsize</span></td><td>$3.8M</td><td><span class="bdg g">&#8593; +12%</span></td></tr>
                <tr><td>3</td><td>KORD &#8594; KTEB</td><td><span class="bdg sky">Large Cabin</span></td><td>$3.5M</td><td><span class="bdg r">&#8595; -4%</span></td></tr>
                <tr><td>4</td><td>KMIA &#8594; KPBI</td><td><span class="bdg sky">Light</span></td><td>$2.9M</td><td><span class="bdg g">&#8593; +22%</span></td></tr>
                <tr><td>5</td><td>KBOS &#8594; KTEB</td><td><span class="bdg sky">Midsize</span></td><td>$2.7M</td><td><span class="bdg g">&#8593; +8%</span></td></tr>
              </tbody>
            </table>
            <p style="margin-top:10px;font-size:12px;color:var(--t3)">Data as of May 16, 2025</p>
            <div class="xbtns">
              <button class="xbtn" title="Download as Excel spreadsheet"><span class="material-symbols-rounded">table_chart</span>Excel</button>
              <button class="xbtn" title="Visualize as chart"><span class="material-symbols-rounded">insert_chart</span>Graph</button>
              <button class="xbtn" title="Export as PDF document"><span class="material-symbols-rounded">picture_as_pdf</span>PDF</button>
              <button class="xbtn" title="Add to PowerPoint presentation"><span class="material-symbols-rounded">slideshow</span>PPT</button>
            </div>
          </div>
          <div class="macts2">
            <button class="abtn2" title="Copy"><span class="material-symbols-rounded">content_copy</span></button>
            <button class="abtn2" title="Thumbs up"><span class="material-symbols-rounded">thumb_up</span></button>
            <button class="abtn2" title="Thumbs down"><span class="material-symbols-rounded">thumb_down</span></button>
          </div>
        </div>
      </div>
    </div>
    <div class="iarea">
      <div class="iwrap">
        <div class="ibox">
          <textarea class="ita" placeholder="Ask a follow-up question..." rows="4"></textarea>
          <button class="sbtn"><span class="material-symbols-rounded">arrow_upward</span></button>
        </div>
        <div class="idisc">WheelsUp AI may make mistakes. Always verify critical data.</div>
      </div>
    </div>
  </div>
</div>
</div>

<!-- SCREEN 4: GRAPH VIEW -->
<div id="screen-graph" class="screen">
<div class="shell">
  <aside class="sb">
    <div class="sbh">
      <svg class="wumark" viewBox="0 0 116 20" xmlns="http://www.w3.org/2000/svg"><text x="0" y="17" font-family="Arial Black,Arial,sans-serif" font-weight="900" font-style="italic" font-size="17" fill="#FFFFFF">WHEELS UP</text></svg>
      <button class="colbtn" onclick="toggleSidebar(this)" title="Collapse sidebar"><span class="material-symbols-rounded">left_panel_close</span></button>
    </div>
    <div class="sbnav"><button class="sbbtn"><span class="material-symbols-rounded">add_comment</span><span>New chat</span></button></div>
    <div class="sbsec">Recent</div>
    <div class="sbhist">
      <div class="hi act"><span class="hi-ico material-symbols-rounded">insert_chart</span><span class="hi-text">Revenue graph by route</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Top routes by revenue YTD</span></div>
      <div class="hi"><span class="hi-ico material-symbols-rounded">forum</span><span class="hi-text">Fleet utilization by aircraft type</span></div>
    </div>
    <div class="sbfoot"><div class="urow"><div class="av">JD</div><div class="uinfo"><div class="uname">Javier Dela Cruz</div><div class="uemail">javier.delacruz@wheelsup.com</div></div></div></div>
  </aside>
  <div class="main">
    <div class="chdr">
      <div class="chdr-title">Top routes by revenue YTD - Graph</div>
      <div class="chdr-acts">
        <button class="ibtn" title="Download"><span class="material-symbols-rounded">download</span></button>
        <button class="ibtn" title="More options"><span class="material-symbols-rounded">more_vert</span></button>
      </div>
    </div>
    <div class="marea">
      <div class="graph-shell">
        <section class="graph-card" aria-labelledby="route-revenue-chart-title">
          <div class="graph-head">
            <div>
              <div id="route-revenue-chart-title" class="graph-title">Route Revenue Analytics</div>
              <div class="graph-sub">Separate bar and line graph mockups. In production, both should be generated from chart-ready query results.</div>
            </div>
            <div class="graph-legend" aria-label="Chart legend">
              <span><i class="legend-dot" style="background:#039BE5"></i>Revenue</span>
              <span><i class="legend-dot" style="background:#4ADE80"></i>Flights</span>
            </div>
          </div>
          <svg class="chart-svg bar-chart" viewBox="0 0 760 360" role="img" aria-labelledby="route-revenue-chart-title route-revenue-chart-desc" xmlns="http://www.w3.org/2000/svg">
            <desc id="route-revenue-chart-desc">Bar chart comparing YTD revenue and flight count for five private aviation routes.</desc>
            <defs>
              <linearGradient id="revGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#4DC3F7"/>
                <stop offset="1" stop-color="#039BE5"/>
              </linearGradient>
              <linearGradient id="flightGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#86EFAC"/>
                <stop offset="1" stop-color="#22C55E"/>
              </linearGradient>
            </defs>

            <g stroke="rgba(200,212,228,.16)" stroke-width="1">
              <line x1="92" y1="56" x2="700" y2="56"/>
              <line x1="92" y1="110" x2="700" y2="110"/>
              <line x1="92" y1="164" x2="700" y2="164"/>
              <line x1="92" y1="218" x2="700" y2="218"/>
              <line x1="92" y1="272" x2="700" y2="272"/>
            </g>

            <g class="axis-label">
              <text x="46" y="60">$4M</text>
              <text x="46" y="114">$3M</text>
              <text x="46" y="168">$2M</text>
              <text x="46" y="222">$1M</text>
              <text x="52" y="276">$0</text>
            </g>

            <line x1="92" y1="272" x2="700" y2="272" stroke="rgba(200,212,228,.28)" stroke-width="1.5"/>

            <g>
              <rect x="126" y="45" width="42" height="227" rx="7" fill="url(#revGradient)"/>
              <rect x="173" y="103" width="24" height="169" rx="6" fill="url(#flightGradient)" opacity=".82"/>
              <text x="147" y="34" text-anchor="middle" class="chart-value">$4.2M</text>
              <text x="162" y="304" text-anchor="middle" class="chart-label">KTEB-KMIA</text>
            </g>
            <g>
              <rect x="246" y="67" width="42" height="205" rx="7" fill="url(#revGradient)"/>
              <rect x="293" y="117" width="24" height="155" rx="6" fill="url(#flightGradient)" opacity=".82"/>
              <text x="267" y="56" text-anchor="middle" class="chart-value">$3.8M</text>
              <text x="282" y="304" text-anchor="middle" class="chart-label">KLAX-KSFO</text>
            </g>
            <g>
              <rect x="366" y="83" width="42" height="189" rx="7" fill="url(#revGradient)"/>
              <rect x="413" y="142" width="24" height="130" rx="6" fill="url(#flightGradient)" opacity=".82"/>
              <text x="387" y="72" text-anchor="middle" class="chart-value">$3.5M</text>
              <text x="402" y="304" text-anchor="middle" class="chart-label">KORD-KTEB</text>
            </g>
            <g>
              <rect x="486" y="115" width="42" height="157" rx="7" fill="url(#revGradient)"/>
              <rect x="533" y="57" width="24" height="215" rx="6" fill="url(#flightGradient)" opacity=".82"/>
              <text x="507" y="104" text-anchor="middle" class="chart-value">$2.9M</text>
              <text x="522" y="304" text-anchor="middle" class="chart-label">KMIA-KPBI</text>
            </g>
            <g>
              <rect x="606" y="126" width="42" height="146" rx="7" fill="url(#revGradient)"/>
              <rect x="653" y="159" width="24" height="113" rx="6" fill="url(#flightGradient)" opacity=".82"/>
              <text x="627" y="115" text-anchor="middle" class="chart-value">$2.7M</text>
              <text x="642" y="304" text-anchor="middle" class="chart-label">KBOS-KTEB</text>
            </g>

            <text x="92" y="338" class="axis-label">Revenue bars use left axis. Green bars show relative flight count to reveal volume vs. route value.</text>
          </svg>

          <div class="chart-section-title">Average Revenue per Flight Trend</div>
          <svg class="chart-svg line-chart" viewBox="0 0 760 270" role="img" aria-labelledby="avg-revenue-line-title avg-revenue-line-desc" xmlns="http://www.w3.org/2000/svg">
            <title id="avg-revenue-line-title">Average revenue per flight line chart</title>
            <desc id="avg-revenue-line-desc">Independent line chart showing average revenue per flight across the same top five routes.</desc>
            <g stroke="rgba(200,212,228,.16)" stroke-width="1">
              <line x1="92" y1="42" x2="700" y2="42"/>
              <line x1="92" y1="88" x2="700" y2="88"/>
              <line x1="92" y1="134" x2="700" y2="134"/>
              <line x1="92" y1="180" x2="700" y2="180"/>
              <line x1="92" y1="226" x2="700" y2="226"/>
            </g>
            <g class="axis-label">
              <text x="38" y="46">$15K</text>
              <text x="38" y="92">$12K</text>
              <text x="44" y="138">$9K</text>
              <text x="44" y="184">$6K</text>
              <text x="44" y="230">$3K</text>
            </g>
            <line x1="92" y1="226" x2="700" y2="226" stroke="rgba(200,212,228,.28)" stroke-width="1.5"/>
            <polyline points="162,66 282,73 402,50 522,164 642,79" fill="none" stroke="#FBBF24" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
            <g>
              <circle class="line-point" cx="162" cy="66" r="5"/>
              <circle class="line-point" cx="282" cy="73" r="5"/>
              <circle class="line-point" cx="402" cy="50" r="5"/>
              <circle class="line-point" cx="522" cy="164" r="5"/>
              <circle class="line-point" cx="642" cy="79" r="5"/>
              <text x="162" y="52" text-anchor="middle" class="line-label">$13.5K</text>
              <text x="282" y="59" text-anchor="middle" class="line-label">$13.2K</text>
              <text x="402" y="36" text-anchor="middle" class="line-label">$14.5K</text>
              <text x="522" y="150" text-anchor="middle" class="line-label">$7.3K</text>
              <text x="642" y="65" text-anchor="middle" class="line-label">$12.9K</text>
            </g>
            <g class="chart-label">
              <text x="162" y="254" text-anchor="middle">KTEB-KMIA</text>
              <text x="282" y="254" text-anchor="middle">KLAX-KSFO</text>
              <text x="402" y="254" text-anchor="middle">KORD-KTEB</text>
              <text x="522" y="254" text-anchor="middle">KMIA-KPBI</text>
              <text x="642" y="254" text-anchor="middle">KBOS-KTEB</text>
            </g>
          </svg>
        </section>

        <aside class="insight-panel" aria-label="Graph insights">
          <div class="insight-title">Key takeaways</div>
          <div class="insight"><strong>$17.1M</strong><span>Total revenue in top 5 routes</span></div>
          <div class="insight"><strong>KTEB-KMIA</strong><span>Highest revenue route YTD</span></div>
          <div class="insight"><strong>KMIA-KPBI</strong><span>Highest flight volume among top routes</span></div>
          <div class="insight"><strong>$14.5K</strong><span>Highest average revenue per flight: KORD-KTEB</span></div>
          <div class="insight"><strong>Large Cabin</strong><span>Dominates high-yield routes</span></div>
        </aside>
      </div>
    </div>
  </div>
</div>
</div>

<!-- SCREEN 5: COLLAPSED SIDEBAR -->
<div id="screen-collapsed" class="screen">
<div class="shell">
  <aside class="sb col">
    <div class="sbh">
      <button class="colbtn" onclick="toggleSidebar(this)" title="Expand sidebar"><span class="material-symbols-rounded">left_panel_open</span></button>
    </div>
    <div class="sbnav"><button class="sbbtn"><span class="material-symbols-rounded">add_comment</span></button></div>
    <div class="sbhist">
      <div class="hi act"><span class="material-symbols-rounded">forum</span></div>
      <div class="hi"><span class="material-symbols-rounded">forum</span></div>
      <div class="hi"><span class="material-symbols-rounded">forum</span></div>
      <div class="hi"><span class="material-symbols-rounded">forum</span></div>
    </div>
    <div class="sbfoot"><div class="urow"><div class="av">JD</div></div></div>
  </aside>
  <div class="main">
    <div class="chdr">
      <div class="chdr-title">Top routes by revenue YTD</div>
      <div class="chdr-acts">
        <button class="ibtn"><span class="material-symbols-rounded">more_vert</span></button>
      </div>
    </div>
    <div class="marea">
      <div class="minner">
        <div style="text-align:center;padding:40px 20px;color:var(--t3)">
          <div class="material-symbols-rounded" style="font-size:34px;margin-bottom:12px;color:var(--wu-sky)">left_panel_open</div>
          <div style="font-size:13px">Sidebar is collapsed. Click the panel icon to open it.</div>
          <div style="margin-top:20px;font-size:12px;color:var(--t4)">This view shows the rail-only mode — icons only, no labels.</div>
        </div>
      </div>
    </div>
    <div class="iarea">
      <div class="iwrap">
        <div class="ibox">
          <textarea class="ita" placeholder="Ask about flights, revenue, members…" rows="1"></textarea>
          <button class="sbtn"><span class="material-symbols-rounded">arrow_upward</span></button>
        </div>
        <div class="idisc">WheelsUp AI may make mistakes. Always verify critical data.</div>
      </div>
    </div>
  </div>
</div>
</div>

<!-- SCREEN 6: DESIGN TOKENS -->
<div id="screen-tokens" class="screen">
<div class="tscreen">
  <div class="th1">AI Agent — Design Tokens</div>
  <div class="tsub">Brand palette, app identity, typography, and component reference for the chat UI redesign.</div>

  <div class="tsec">
    <div class="tsec-t">Brand Colors (from wheelsup.com)</div>
    <div class="swatches">
      <div class="sw"><div class="swc" style="background:#041C46"></div><div><div class="swn">Darkest Navy</div><div class="swh">--wu-darkest · #041C46</div></div></div>
      <div class="sw"><div class="swc" style="background:#202530"></div><div><div class="swn">Dark (Primary BG)</div><div class="swh">--wu-dark · #202530</div></div></div>
      <div class="sw"><div class="swc" style="background:#1A2035"></div><div><div class="swn">Surface 1</div><div class="swh">--s1 · #1A2035</div></div></div>
      <div class="sw"><div class="swc" style="background:#2D4266"></div><div><div class="swn">Navy (Cards / Nav)</div><div class="swh">--wu-navy · #2D4266</div></div></div>
      <div class="sw"><div class="swc" style="background:#344E72"></div><div><div class="swn">Surface 3 (Hover)</div><div class="swh">--s3 · #344E72</div></div></div>
      <div class="sw"><div class="swc" style="background:#507BA3"></div><div><div class="swn">Blue Accent</div><div class="swh">--wu-blue · #507BA3</div></div></div>
      <div class="sw"><div class="swc" style="background:#039BE5"></div><div><div class="swn">Sky (CTA / Accent)</div><div class="swh">--wu-sky · #039BE5</div></div></div>
      <div class="sw"><div class="swc" style="background:#4DC3F7"></div><div><div class="swn">Sky Hover</div><div class="swh">--gl · #4DC3F7</div></div></div>
      <div class="sw"><div class="swc" style="background:#FFFFFF;border:1px solid rgba(0,0,0,.1)"></div><div><div class="swn">White</div><div class="swh">--t · #FFFFFF</div></div></div>
      <div class="sw"><div class="swc" style="background:#C8D4E4"></div><div><div class="swn">Text 2</div><div class="swh">--t2 · #C8D4E4</div></div></div>
      <div class="sw"><div class="swc" style="background:#7A96B8"></div><div><div class="swn">Text 3 (Muted)</div><div class="swh">--t3 · #7A96B8</div></div></div>
      <div class="sw"><div class="swc" style="background:#4A6080"></div><div><div class="swn">Text 4 (Dim)</div><div class="swh">--t4 · #4A6080</div></div></div>
      <div class="sw"><div class="swc" style="background:#4ADE80"></div><div><div class="swn">Success</div><div class="swh">.bdg.g · #4ADE80</div></div></div>
      <div class="sw"><div class="swc" style="background:#F87171"></div><div><div class="swn">Danger</div><div class="swh">.bdg.r · #F87171</div></div></div>
    </div>
  </div>

  <div class="tsec">
    <div class="tsec-t">Typography Scale</div>
    <div class="trow"><span class="tlbl">h1 / 26px</span><span style="font-size:26px;font-weight:700;letter-spacing:-.02em">Ask AI Agent</span></div>
    <div class="trow"><span class="tlbl">h2 / 20px</span><span style="font-size:20px;font-weight:700">Top Routes by Revenue</span></div>
    <div class="trow"><span class="tlbl">h3 / 16px</span><span style="font-size:16px;font-weight:600">Flight Operations Summary</span></div>
    <div class="trow"><span class="tlbl">body / 13px</span><span style="font-size:13px;color:var(--t2)">Here are the top 10 routes by revenue year-to-date, broken down by fleet type.</span></div>
    <div class="trow"><span class="tlbl">small / 11px</span><span style="font-size:11px;color:var(--t3)">AI Agent may make mistakes. Always verify critical data.</span></div>
    <div class="trow"><span class="tlbl">label / 10px</span><span style="font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--t4)">Recent Conversations</span></div>
  </div>

  <div class="tsec">
    <div class="tsec-t">App Identity</div>
    <div class="crow">
      <span class="clbl">Browser tab</span>
      <div class="browser-tab-token">
        <span class="upmark sm">
          <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><text x="31.5" y="42.5" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="31" font-weight="900" font-style="italic" letter-spacing="-4.5" fill="#041C46">UP</text></svg>
        </span>
        <span style="font-size:18px;font-weight:500">AI Agent</span>
        <span class="material-symbols-rounded tab-close">close</span>
      </div>
      <div style="font-size:11px;color:var(--t4);margin-left:8px">Use <code style="font-family:monospace;color:var(--t2)">favicon.svg</code> and document title <code style="font-family:monospace;color:var(--t2)">AI Agent</code>.</div>
    </div>
    <div class="crow">
      <span class="clbl">App icon</span>
      <span class="upmark sm">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><text x="31.5" y="42.5" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="31" font-weight="900" font-style="italic" letter-spacing="-4.5" fill="#041C46">UP</text></svg>
      </span>
      <span class="upmark md">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><text x="31.5" y="42.5" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="31" font-weight="900" font-style="italic" letter-spacing="-4.5" fill="#041C46">UP</text></svg>
      </span>
      <span class="upmark lg">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><text x="31.5" y="42.5" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="31" font-weight="900" font-style="italic" letter-spacing="-4.5" fill="#041C46">UP</text></svg>
      </span>
      <div style="font-size:11px;color:var(--t4);margin-left:8px">UP mark — navy on white tile — 28px / 48px / 64px</div>
    </div>
    <div class="crow">
      <span class="clbl">Sidebar brand</span>
      <div style="height:42px;display:flex;align-items:center;background:#041C46;border-radius:8px;padding:0 16px">
        <svg class="wumark" viewBox="0 0 116 20" xmlns="http://www.w3.org/2000/svg"><text x="0" y="17" font-family="Arial Black,Arial,sans-serif" font-weight="900" font-style="italic" font-size="17" fill="#FFFFFF">WHEELS UP</text></svg>
      </div>
      <div style="font-size:11px;color:var(--t4);margin-left:8px">Keep the full Wheels Up wordmark for branded sidebar/header surfaces.</div>
    </div>
  </div>

  <div class="tsec">
    <div class="tsec-t">Components</div>
    <div class="crow">
      <span class="clbl">Badges</span>
      <span class="bdg g">On Time</span>
      <span class="bdg r">Delayed</span>
      <span class="bdg sky">Large Cabin</span>
    </div>
    <div class="crow">
      <span class="clbl">Buttons</span>
      <button class="sbtn" style="position:relative;width:auto;height:auto;border-radius:20px;padding:7px 16px;font-size:13px;font-family:inherit">Primary (Sky Blue)</button>
      <button class="ibtn" style="width:auto;height:auto;padding:6px 14px;font-size:12px">Secondary</button>
      <button class="abtn">Action</button>
    </div>
    <div class="crow">
      <span class="clbl">Tool Pills</span>
      <span class="tpill"><span class="spin"></span>query_flights_genie — Running…</span>
      <span class="tpill done">✓ search_flights_context — Done</span>
    </div>
    <div class="crow">
      <span class="clbl">Input</span>
      <div class="ibox" style="max-width:400px;flex:1">
        <textarea class="ita" placeholder="Ask about flights, revenue, members…" rows="1" style="font-size:13px"></textarea>
        <button class="sbtn"><span class="material-symbols-rounded">arrow_upward</span></button>
      </div>
    </div>
  </div>

  <div class="tsec">
    <div class="tsec-t">Spacing &amp; Radius</div>
    <div class="crow">
      <span class="clbl">Border Radius</span>
      <div style="width:32px;height:32px;background:var(--s2);border:1px solid var(--bd);border-radius:4px"></div>
      <div style="font-size:10px;color:var(--t4)">4px (sm)</div>
      <div style="width:32px;height:32px;background:var(--s2);border:1px solid var(--bd);border-radius:8px"></div>
      <div style="font-size:10px;color:var(--t4)">8px (default)</div>
      <div style="width:32px;height:32px;background:var(--s2);border:1px solid var(--bd);border-radius:12px"></div>
      <div style="font-size:10px;color:var(--t4)">12px (lg)</div>
      <div style="width:32px;height:32px;background:var(--s2);border:1px solid var(--bd);border-radius:20px"></div>
      <div style="font-size:10px;color:var(--t4)">20px (xl / input)</div>
      <div style="width:32px;height:32px;background:var(--s2);border:1px solid var(--bd);border-radius:50%"></div>
      <div style="font-size:10px;color:var(--t4)">50% (circle / send btn)</div>
    </div>
  </div>

  <div style="padding:16px;background:var(--gd2);border:1px solid rgba(3,155,229,.2);border-radius:var(--r);font-size:12px;color:var(--t3)">
    <strong style="color:var(--g)">Implementation note:</strong> These tokens map to CSS custom properties in <code style="font-family:monospace;color:var(--t2)">index.css</code>. Replace the existing Databricks DuBois blue palette (<code style="font-family:monospace">--color-blue-*</code>, <code style="font-family:monospace">--primary</code>) with the WheelsUp navy/sky palette above. The browser tab should use <code style="font-family:monospace">AI Agent</code> plus the white <code style="font-family:monospace">UP</code> favicon, while sidebar branding uses <code style="font-family:monospace">--wu-darkest (#041C46)</code> and the full Wheels Up wordmark. The primary CTA accent is <code style="font-family:monospace">--wu-sky (#039BE5)</code>.
  </div>
</div>
</div>

  `);
});

// Dark/light mode toggle
function toggleMode() {
  const isLight = document.body.classList.toggle('light');
  const knob = document.getElementById('mode-knob');
  const lbl = document.getElementById('mode-lbl');
  if (knob) knob.style.left = isLight ? '16px' : '2px';
  if (lbl) lbl.textContent = isLight ? 'Light' : 'Dark';
}
window.toggleMode = toggleMode;

// Tab switching
function show(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.mtab').forEach(t => t.classList.remove('active'));
  const el = document.getElementById('screen-' + id);
  if (el) el.classList.add('active');
  const tabs = document.querySelectorAll('.mtab');
  const map = {greeting:0, chat:1, appstyle:2, graph:3, collapsed:4, tokens:5};
  if (tabs[map[id]]) tabs[map[id]].classList.add('active');
}
window.show = show;
