// Exercise the standalone output layout used by the frontend Docker runner.
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const results = [];
for (const [app, port, routes] of [
  ["customer-web", 13001, ["/", "/search", "/booking/checkout", "/my-bookings"]],
  ["admin-dashboard", 13000, ["/", "/login", "/Hotels", "/Rooms", "/Bookings", "/Payments", "/Users", "/Notifications"]],
]) {
  const appDir = path.join(root, "front-end/apps", app);
  const standalone = path.join(appDir, ".next/standalone/apps", app);
  await fs.cp(path.join(appDir, ".next/static"), path.join(standalone, ".next/static"), { recursive: true });
  const child = spawn(process.execPath, [path.join(standalone, "server.js")], {
    cwd: standalone, env: { ...process.env, PORT: String(port), HOSTNAME: "127.0.0.1" }, stdio: "ignore",
  });
  try {
    let ready = false;
    for (let i = 0; i < 50 && !ready; i++) {
      try { ready = (await fetch(`http://127.0.0.1:${port}`)).ok; } catch {}
      if (!ready) await new Promise(resolve => setTimeout(resolve, 200));
    }
    if (!ready) throw new Error(`${app} did not start`);
    for (const route of routes) {
      const response = await fetch(`http://127.0.0.1:${port}${route}`);
      if (!response.ok) throw new Error(`${app} ${route}: ${response.status}`);
      const html = await response.text();
      const asset = html.match(/(?:src|href)="([^"\s]*\/_next\/static\/[^"\s]+)"/);
      if (asset) {
        const staticResponse = await fetch(new URL(asset[1].replaceAll("&amp;", "&"), `http://127.0.0.1:${port}`));
        if (!staticResponse.ok) throw new Error(`${app} static asset: ${staticResponse.status}`);
      }
      results.push({ app, route, status: "PASS" });
      console.log(`PASS: ${app} ${route} and static assets`);
    }
  } finally {
    child.kill();
    await new Promise(resolve => { if (child.exitCode !== null) resolve(); else child.once("exit", resolve); });
  }
}
await fs.writeFile(path.join(root, "logs/frontend-server-results.json"), JSON.stringify(results, null, 2));
