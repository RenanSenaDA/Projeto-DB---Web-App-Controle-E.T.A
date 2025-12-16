const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const EXCLUDES = new Set([
  path.join(ROOT, 'styles', 'globals.css'),
  path.join(ROOT, 'node_modules'),
]);
const ALLOWED_EXT = new Set(['.ts', '.tsx', '.js', '.jsx', '.css', '.scss', '.mdx']);
const HEX_RE = /#[0-9a-fA-F]{3,6}\b/g;

let found = [];

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if ([...EXCLUDES].some(ex => full.startsWith(ex))) continue;
    if (entry.isDirectory()) {
      walk(full);
    } else {
      const ext = path.extname(entry.name);
      if (!ALLOWED_EXT.has(ext)) continue;
      const content = fs.readFileSync(full, 'utf8');
      const matches = content.match(HEX_RE);
      if (matches) {
        // ignore CSS variables definitions that are allowed inside globals.css (already excluded)
        for (const m of matches) {
          found.push({ file: full, match: m });
        }
      }
    }
  }
}

walk(ROOT);

if (found.length > 0) {
  console.error('Hardcoded hex colors detectados:');
  for (const f of found) {
    console.error(`${f.file}: ${f.match}`);
  }
  process.exit(1);
} else {
  console.log('OK: Nenhum hex hardcoded encontrado fora de styles/globals.css');
}

