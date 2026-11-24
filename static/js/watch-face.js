/* The Ralfiz analog watch face, drawn on a <canvas>. Shared by the full world clock
   page and the single clock on the dashboard. opts: {night, day, accent, label, sub}. */
(function(){
  function drawWatch(cv, h, m, s, opts){
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const css = cv.clientWidth || 176;
    if (cv.width !== Math.round(css*dpr)) { cv.width = cv.height = Math.round(css*dpr); }
    const ctx = cv.getContext("2d"), W = cv.width, R = W/2;
    ctx.setTransform(1,0,0,1,0,0); ctx.clearRect(0,0,W,W);
    ctx.translate(R, R);
    const night = opts.night;

    // case shadow
    ctx.save(); ctx.shadowColor = "rgba(10,18,30,.35)"; ctx.shadowBlur = R*.09; ctx.shadowOffsetY = R*.04;
    ctx.beginPath(); ctx.arc(0,0,R*.94,0,Math.PI*2); ctx.fillStyle = "#8C949E"; ctx.fill(); ctx.restore();

    // brushed steel bezel
    let g = ctx.createLinearGradient(-R, -R, R, R);
    g.addColorStop(0, "#FAFBFC"); g.addColorStop(.3, "#B7BFC9"); g.addColorStop(.5, "#EEF1F4");
    g.addColorStop(.72, "#8D96A1"); g.addColorStop(1, "#D9DEE4");
    ctx.beginPath(); ctx.arc(0,0,R*.94,0,Math.PI*2); ctx.fillStyle = g; ctx.fill();
    // inner bevel
    g = ctx.createLinearGradient(-R, -R, R, R);
    g.addColorStop(0, "#6F7884"); g.addColorStop(1, "#F4F6F8");
    ctx.beginPath(); ctx.arc(0,0,R*.85,0,Math.PI*2); ctx.fillStyle = g; ctx.fill();

    // dial
    const FR = R*.81;
    g = ctx.createRadialGradient(-FR*.3, -FR*.35, FR*.1, 0, 0, FR);
    if (night){ g.addColorStop(0, "#26375A"); g.addColorStop(1, "#0B1424"); }
    else { g.addColorStop(0, "#FFFFFF"); g.addColorStop(1, "#DCE2EA"); }
    ctx.beginPath(); ctx.arc(0,0,FR,0,Math.PI*2); ctx.fillStyle = g; ctx.fill();
    // sunray guilloché
    ctx.save(); ctx.globalAlpha = night ? .05 : .045; ctx.strokeStyle = night ? "#FFFFFF" : "#1A2433"; ctx.lineWidth = 1;
    for (let i = 0; i < 120; i++){ const a = i*Math.PI/60; ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(FR*Math.cos(a), FR*Math.sin(a)); ctx.stroke(); }
    ctx.restore();

    const ink = night ? "#DCE6F5" : "#1C2735";
    const lume = "#BFF2D8";
    // minute track
    for (let i = 0; i < 60; i++){
      if (i % 5 === 0) continue;
      const a = i*Math.PI/30;
      ctx.beginPath(); ctx.moveTo(Math.sin(a)*FR*.92, -Math.cos(a)*FR*.92); ctx.lineTo(Math.sin(a)*FR*.97, -Math.cos(a)*FR*.97);
      ctx.strokeStyle = ink; ctx.globalAlpha = .55; ctx.lineWidth = R*.012; ctx.stroke(); ctx.globalAlpha = 1;
    }
    // applied hour indices
    for (let i = 0; i < 12; i++){
      if (i === 3) continue; // date window
      ctx.save(); ctx.rotate(i*Math.PI/6);
      const w = i === 0 ? R*.035 : R*.028, len = i % 3 === 0 ? FR*.2 : FR*.15;
      const draw = x => {
        ctx.save(); ctx.shadowColor = "rgba(0,0,0,.35)"; ctx.shadowBlur = R*.02; ctx.shadowOffsetY = R*.01;
        g = ctx.createLinearGradient(x-w, 0, x+w, 0); g.addColorStop(0, "#F7F9FB"); g.addColorStop(.5, "#8C96A3"); g.addColorStop(1, "#E3E7EC");
        ctx.fillStyle = g; ctx.fillRect(x-w/2, -FR*.95, w, len); ctx.restore();
        if (night){ ctx.fillStyle = lume; ctx.fillRect(x-w/4, -FR*.93, w/2, len*.8); }
      };
      if (i === 0){ draw(-R*.03); draw(R*.03); } else draw(0);
      ctx.restore();
    }
    // date window at 3
    const dw = R*.2, dh = R*.15, dx = FR*.62;
    ctx.save(); ctx.shadowColor = "rgba(0,0,0,.4)"; ctx.shadowBlur = R*.02;
    ctx.fillStyle = "#8C96A3"; ctx.fillRect(dx-dw/2-1, -dh/2-1, dw+2, dh+2); ctx.restore();
    ctx.fillStyle = "#FBFBF8"; ctx.fillRect(dx-dw/2, -dh/2, dw, dh);
    ctx.fillStyle = "#1C2735"; ctx.font = `600 ${R*.11}px "JetBrains Mono", monospace`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(String(opts.day), dx, R*.005);

    // wordmark + zone
    ctx.fillStyle = ink; ctx.textAlign = "center";
    ctx.font = `700 ${R*.085}px "Bricolage Grotesque", sans-serif`; ctx.fillText("RALFIZ", 0, -FR*.38);
    ctx.globalAlpha = .7; ctx.font = `500 ${R*.065}px "JetBrains Mono", monospace`; ctx.fillText(opts.label, 0, FR*.4);
    ctx.globalAlpha = .55; ctx.font = `500 ${R*.05}px "Instrument Sans", sans-serif`; ctx.fillText(opts.sub, 0, FR*.52);
    ctx.globalAlpha = 1;

    // hands
    const hand = (angle, len, tail, wBase, wTip, fill, lumeOn) => {
      ctx.save(); ctx.rotate(angle);
      ctx.shadowColor = "rgba(0,0,0,.38)"; ctx.shadowBlur = R*.035; ctx.shadowOffsetX = R*.018; ctx.shadowOffsetY = R*.03;
      ctx.beginPath(); ctx.moveTo(-wBase/2, tail); ctx.lineTo(-wTip/2, -len); ctx.lineTo(0, -len - wTip); ctx.lineTo(wTip/2, -len); ctx.lineTo(wBase/2, tail); ctx.closePath();
      g = ctx.createLinearGradient(-wBase, 0, wBase, 0); g.addColorStop(0, fill[0]); g.addColorStop(.5, fill[1]); g.addColorStop(1, fill[2]);
      ctx.fillStyle = g; ctx.fill(); ctx.restore();
      if (lumeOn){ ctx.save(); ctx.rotate(angle); ctx.fillStyle = lume; ctx.globalAlpha = .9;
        ctx.fillRect(-wTip/4, -len*.92, wTip/2, len*.55); ctx.restore(); }
    };
    const steel = night ? ["#E9EEF4","#AEB8C5","#F5F7FA"] : ["#2A3647","#0E1520","#3A475A"];
    const ha = (h%12 + m/60 + s/3600) * Math.PI/6, ma = (m + s/60) * Math.PI/30, sa = s * Math.PI/30;
    hand(ha, FR*.5, R*.12, R*.07, R*.045, steel, night);
    hand(ma, FR*.78, R*.14, R*.055, R*.03, steel, night);
    // second hand with counterweight
    ctx.save(); ctx.rotate(sa);
    ctx.shadowColor = "rgba(0,0,0,.35)"; ctx.shadowBlur = R*.02; ctx.shadowOffsetX = R*.012; ctx.shadowOffsetY = R*.02;
    ctx.strokeStyle = opts.accent; ctx.lineWidth = R*.016; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(0, R*.22); ctx.lineTo(0, -FR*.9); ctx.stroke();
    ctx.fillStyle = opts.accent; ctx.beginPath(); ctx.arc(0, R*.2, R*.035, 0, Math.PI*2); ctx.fill();
    ctx.beginPath(); ctx.arc(0, -FR*.68, R*.026, 0, Math.PI*2); ctx.fill();
    ctx.restore();
    // center cap
    g = ctx.createRadialGradient(-R*.01, -R*.01, 0, 0, 0, R*.045);
    g.addColorStop(0, "#FFFFFF"); g.addColorStop(1, "#7A8592");
    ctx.beginPath(); ctx.arc(0,0,R*.042,0,Math.PI*2); ctx.fillStyle = g; ctx.fill();
    ctx.beginPath(); ctx.arc(0,0,R*.016,0,Math.PI*2); ctx.fillStyle = opts.accent; ctx.fill();

    // sapphire glass reflection
    ctx.save(); ctx.beginPath(); ctx.arc(0,0,FR,0,Math.PI*2); ctx.clip();
    g = ctx.createLinearGradient(-FR, -FR, FR*.2, FR*.2);
    g.addColorStop(0, "rgba(255,255,255,.28)"); g.addColorStop(.45, "rgba(255,255,255,.04)"); g.addColorStop(.46, "rgba(255,255,255,0)");
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(-FR*.25, -FR*.3, FR*1.05, FR*.8, -Math.PI/4, 0, Math.PI*2); ctx.fill();
    ctx.restore();
  }

  window.drawWatch = drawWatch;
})();
