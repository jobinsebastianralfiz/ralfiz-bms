// verify-toolkit.js - run with: node verify-toolkit.js
// Checks the AB-400 developer toolkit. Needs Node.js 18 or later. No npm packages required.
"use strict";
const { execSync } = require("child_process");
const fs = require("fs");

function run(cmd) {
  try {
    return { ok: true, out: execSync(cmd, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], timeout: 120000 }) };
  } catch (err) {
    return { ok: false, out: String(err.stdout || "") + String(err.stderr || err.message) };
  }
}

function majorOf(text) {
  const m = /(\d+)\.\d+/.exec(text);
  return m ? parseInt(m[1], 10) : 0;
}

const checks = [
  {
    name: ".NET SDK 8 or later",
    test: function () {
      const r = run("dotnet --version");
      return { pass: r.ok && majorOf(r.out) >= 8, detail: r.out.trim() };
    }
  },
  {
    name: "Node.js 20 or later",
    test: function () {
      const major = majorOf(process.version);
      return { pass: major >= 20, detail: process.version };
    }
  },
  {
    name: "pac CLI on the path",
    test: function () {
      const r = run("pac help");
      const pass = /PowerPlatform CLI/i.test(r.out);
      return { pass: pass, detail: pass ? "pac found" : "pac not found - install the extension or the .NET tool" };
    }
  },
  {
    name: "Active pac auth profile",
    test: function () {
      const r = run("pac auth list");
      const active = r.out.split(/\r?\n/).filter(function (l) { return l.indexOf("*") >= 0; });
      return { pass: r.ok && active.length > 0, detail: active.length ? active[0].trim() : "no active profile - run pac auth create" };
    }
  },
  {
    name: "Campus Help Desk solution visible",
    test: function () {
      const r = run("pac solution list");
      const pass = r.ok && /CampusHelpDesk/i.test(r.out);
      return { pass: pass, detail: pass ? "CampusHelpDesk found" : "not found - check pac org who and your profile" };
    }
  },
  {
    name: "Exported solution zip exists",
    test: function () {
      const file = "./out/CampusHelpDesk.zip";
      const pass = fs.existsSync(file) && fs.statSync(file).size > 0;
      return { pass: pass, detail: pass ? file + " (" + fs.statSync(file).size + " bytes)" : "run pac solution export first" };
    }
  }
];

let passed = 0;
checks.forEach(function (c, i) {
  const r = c.test();
  if (r.pass) { passed++; }
  console.log((r.pass ? "PASS " : "FAIL ") + (i + 1) + ". " + c.name + " - " + r.detail);
});

const who = run("pac org who");
if (who.ok) {
  console.log("\npac org who:\n" + who.out.trim());
}
console.log("\nRESULT: " + passed + " of " + checks.length + " checks passed");
process.exitCode = passed === checks.length ? 0 : 1;
