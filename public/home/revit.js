// Builds a logo-free Revit 2025+ style window (see revit.css).
// revitWindow({ file, img, mode: "model" | "cloud", sel: {x,y,w,h} (in %), tip, compact, element })
(function () {
  const I = {
    modify: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 3l12 8-5 1.5L14 19l-2.5 1-2-6.5L5 17z" fill="#d6d7db"/></svg>',
    props: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
    paste: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="6" y="4" width="12" height="17" rx="1.5"/><path d="M9 4V3h6v1"/></svg>',
    join: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 15h9V6h9v9h-9"/></svg>',
    align: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 3v18M8 7h12M8 12h8M8 17h10"/></svg>',
    move: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3v18M3 12h18M12 3l-3 3M12 3l3 3M21 12l-3-3M21 12l-3 3"/></svg>',
    rotate: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 12a7 7 0 1 1-2-4.9M19 4v4h-4"/></svg>',
    mirror: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3v18" stroke-dasharray="2 2"/><path d="M9 7 4 17h5zM15 7l5 10h-5z"/></svg>',
    measure: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 16 16 4l4 4L8 20z"/><path d="M8 12l2 2M11 9l2 2M14 6l2 2"/></svg>',
    view: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    family: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2 21 7v10l-9 5-9-5V7z"/><path d="M3 7l9 5 9-5M12 12v10"/></svg>',
    cloud: '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="9" r="1.3"/><circle cx="10" cy="6" r="1.3"/><circle cx="14" cy="8" r="1.3"/><circle cx="18" cy="11" r="1.3"/><circle cx="8" cy="13" r="1.3"/><circle cx="13" cy="14" r="1.3"/><circle cx="17" cy="17" r="1.3"/><circle cx="9" cy="18" r="1.3"/></svg>',
    save: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 3h11l3 3v15H5z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/></svg>',
    undo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/></svg>',
    redo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="m15 14 5-5-5-5"/><path d="M20 9H10a6 6 0 0 0 0 12h3"/></svg>',
    cube: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3 20 7.5v9L12 21l-8-4.5v-9z"/></svg>',
    sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>',
  };
  const tool = (icon, label) => `<div class="rv-tool">${I[icon]}<span>${label}</span></div>`;
  const sm = (icon, label) => `<div class="rv-tool sm">${I[icon]}<span>${label}</span></div>`;

  window.revitWindow = function (o) {
    const cloud = o.mode === "cloud";
    const el = o.element || { cat: "Mechanical Equipment", fam: "Pump assembly", type: "Centrifugal pump, end suction", mark: "P-101", level: "Level 1" };
    const props = cloud
      ? `<div class="grp">Identity Data</div><div class="rv-r"><span>Name</span><span>Rotterdam.rcp</span></div>
         <div class="grp">Other</div><div class="rv-r"><span>Points</span><span>Linked point cloud</span></div><div class="rv-r"><span>Positioning</span><span>Shared coordinates</span></div><div class="rv-r"><span>Workset</span><span>Point Clouds</span></div>`
      : `<div class="grp">Constraints</div><div class="rv-r"><span>Level</span><span>${el.level}</span></div><div class="rv-r"><span>Host</span><span>Level : ${el.level}</span></div><div class="rv-r"><span>Offset from Host</span><span>0.0</span></div>
         <div class="grp">Identity Data</div><div class="rv-r"><span>Mark</span><span>${el.mark}</span></div><div class="rv-r"><span>Comments</span><span>From scan, LOD 300</span></div>
         <div class="grp">Phasing</div><div class="rv-r"><span>Phase Created</span><span>Existing</span></div><div class="rv-r"><span>Phase Demolished</span><span>None</span></div>`;
    const tree = `
      <div class="x b">Views (all)</div>
      <div class="x" style="--d:1">Floor Plans</div><div class="leaf" style="--d:2">Level 1</div><div class="leaf" style="--d:2">Site</div>
      <div class="x" style="--d:1">3D Views</div><div class="leaf ${cloud ? "" : ""}" style="--d:2">{3D}</div><div class="leaf" style="--d:2">Existing conditions</div>
      <div class="c" style="--d:1">Sections</div><div class="c" style="--d:1">Sheets (all)</div>
      <div class="x b">Families</div>
      <div class="x" style="--d:1">Mechanical Equipment</div>
      <div class="leaf ${cloud ? "" : "sel"}" style="--d:2">${el.fam}</div><div class="leaf" style="--d:2">Heat exchanger</div><div class="leaf" style="--d:2">Vertical vessel</div>
      <div class="c" style="--d:1">Pipes</div><div class="c" style="--d:1">Structural Framing</div><div class="c" style="--d:1">Stairs · Railings</div>
      <div class="c b">Groups</div><div class="${cloud ? "x" : "c"} b">Revit Links</div>${cloud ? '<div class="leaf sel" style="--d:1">Rotterdam.rcp (point cloud)</div>' : ""}`;
    const sel = o.sel && !cloud ? `<div class="rv-sel" style="left:${o.sel.x}%;top:${o.sel.y}%;width:${o.sel.w}%;height:${o.sel.h}%"></div>
      <div class="rv-tip" style="${o.sel.x + o.sel.w > 70 ? `right:${100 - o.sel.x - o.sel.w}%` : `left:${o.sel.x}%`};top:calc(${o.sel.y}% - 22px)">${o.tip || (o.compact ? el.cat + " : " + el.fam : el.cat + " : " + el.fam + " : " + el.type)}</div>` : "";
    return `<div class="rv ${o.compact ? "compact" : ""} ${o.light ? "light" : ""}">
      <div class="rv-title"><span class="rv-app">R</span><span class="rv-qat">${I.save}${I.undo}${I.redo}${I.cube}</span>
        <span class="rv-titletext">Autodesk Revit 2027 - ${o.file || "Rotterdam_existing.rvt"} - 3D View: {3D}</span><span class="rv-win">–&nbsp;&nbsp;▢&nbsp;&nbsp;✕</span></div>
      <div class="rv-tabs"><span class="file">File</span><span>Architecture</span><span>Structure</span><span>Steel</span><span>Systems</span><span>Insert</span><span>Annotate</span><span>Analyze</span><span>Massing &amp; Site</span><span>Collaborate</span><span>View</span><span>Manage</span><span class="on">Modify | ${cloud ? "Point Clouds" : el.cat}</span></div>
      <div class="rv-ribbon">
        <div class="rv-pnl"><div class="rv-tools">${tool("modify", "Modify")}</div><div class="rv-pnl-name">Select</div></div>
        <div class="rv-pnl"><div class="rv-tools">${tool("props", "Properties")}</div><div class="rv-pnl-name">Properties</div></div>
        <div class="rv-pnl"><div class="rv-tools">${tool("paste", "Paste")}<div class="rv-col">${sm("join", "Join")}${sm("align", "Cut")}${sm("measure", "Copy")}</div></div><div class="rv-pnl-name">Clipboard</div></div>
        <div class="rv-pnl"><div class="rv-tools">${tool("align", "Align")}${tool("move", "Move")}${tool("rotate", "Rotate")}${tool("mirror", "Mirror")}</div><div class="rv-pnl-name">Modify</div></div>
        <div class="rv-pnl"><div class="rv-tools">${tool("view", "View")}${tool("measure", "Measure")}</div><div class="rv-pnl-name">View · Measure</div></div>
        <div class="rv-pnl"><div class="rv-tools">${tool("family", "Edit Family")}${tool(cloud ? "cloud" : "family", cloud ? "Point Cloud" : "Create")}</div><div class="rv-pnl-name">Mode</div></div>
      </div>
      <div class="rv-body">
        <div class="rv-left">
          <div class="rv-pal"><div class="rv-pal-h">Properties <i>✕</i></div>
            <div class="rv-type"><span class="ico">${cloud ? I.cloud : I.family}</span><div><b>${cloud ? "Point Cloud" : el.fam}</b><span>${cloud ? "Rotterdam.rcp" : el.type}</span></div></div>
            <div class="rv-filter"><span>${cloud ? "Point Clouds (1)" : el.cat + " (1)"}</span><span>Edit Type</span></div>
            <div class="rv-props">${props}</div></div>
          <div class="rv-pal"><div class="rv-pal-h">Project Browser - ${o.file || "Rotterdam_existing.rvt"} <i>✕</i></div><div class="rv-tree">${tree}</div></div>
        </div>
        <div class="rv-canvas"><img src="${o.img || "/home/media/rotterdam-model.webp"}" alt="">
          <div class="rv-viewtab"><span class="off">Level 1</span><span>{3D}</span></div>${sel}
          <div class="rv-cube"><div class="ring"></div><div class="cube"><div class="f front">FRONT</div><div class="f right">RIGHT</div><div class="f top">TOP</div></div></div>
          <div class="rv-navbar"><i></i><i></i><i></i></div>
        </div>
      </div>
      <div class="rv-viewbar"><span>1 : 100</span><span class="sep"></span>${I.cube}${I.sun}<span class="sep"></span><span>Visual style: Realistic</span><span class="sep"></span><span>Phase: Existing</span></div>
      <div class="rv-status"><b>${cloud ? "Point cloud linked · shared coordinates" : "Click to select, TAB for alternates, CTRL adds, SHIFT unselects."}</b><span>Main Model &nbsp;·&nbsp; :0</span></div>
    </div>`;
  };
})();
