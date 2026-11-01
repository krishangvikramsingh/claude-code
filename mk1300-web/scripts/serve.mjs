#!/usr/bin/env node
/* Zero-dependency static server for dist/, applying the same headers as production.
 *   node scripts/serve.mjs [port]    (default 8080, binds to 127.0.0.1)
 * Exports start() for the tests. */
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIST = path.join(ROOT, 'dist');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
  '.bin': 'application/octet-stream',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
};

// Translate the build's route patterns (Vercel style) into regexes.
const toRegex = (source) => new RegExp('^' + source.replace(/\(\.\*\)/g, '.*').replace(/\\\\\./g, '\\.') + '$');

export async function start(port = 8080, host = '127.0.0.1') {
  const { rules } = JSON.parse(await readFile(path.join(ROOT, '.build/headers.json'), 'utf8'));
  const compiled = rules.map((r) => ({ re: toRegex(r.source), headers: r.headers }));

  const server = createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      let pathname = decodeURIComponent(url.pathname);
      let file = path.normalize(path.join(DIST, pathname));
      if (!file.startsWith(DIST)) throw Object.assign(new Error('forbidden'), { code: 403 });
      let info = await stat(file).catch(() => null);
      if (info && info.isDirectory()) {
        pathname = pathname.replace(/\/?$/, '/') + 'index.html';
        file = path.join(DIST, pathname);
        info = await stat(file).catch(() => null);
      }
      const headers = {};
      for (const r of compiled) if (r.re.test(pathname)) Object.assign(headers, r.headers);
      if (!info) {
        res.writeHead(404, { ...headers, 'Content-Type': MIME['.html'] });
        res.end(await readFile(path.join(DIST, '404.html')).catch(() => 'Not found'));
        return;
      }
      res.writeHead(200, { ...headers, 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
      res.end(req.method === 'HEAD' ? undefined : await readFile(file));
    } catch (e) {
      res.writeHead(e.code === 403 ? 403 : 500).end(e.code === 403 ? 'Forbidden' : 'Server error');
    }
  });
  await new Promise((resolve) => server.listen(port, host, resolve));
  return { server, port: server.address().port, url: `http://${host}:${server.address().port}` };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const { url } = await start(Number(process.argv[2]) || 8080);
  console.log(`Serving dist/ at ${url}  (Ctrl+C to stop)`);
}
