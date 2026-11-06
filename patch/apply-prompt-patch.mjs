#!/usr/bin/env node
// Rejoue le retrait des fragments de comportement du prompt système de Claude Code.
// Lit tri-prompts.tsv (fichier, classe, raison) ; pour chaque ligne RETIRER, garde
// l'en-tête tweakcc (<!-- name/description/ccVersion/variables -->) et vide le corps
// (les variables déclarées restent citées dans une expression qui vaut "").
// tweakcc remplace alors le fragment par une chaîne vide dans le binaire.
// Puis lance tweakcc --apply (version épinglée).
//
// Usage : node apply-prompt-patch.mjs [--dry-run] [--no-apply] [--dir <system-prompts>]
// Le dossier system-prompts doit avoir été extrait par tweakcc (lancer `npx tweakcc@4.4.0` une fois).
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const TWEAKCC = 'tweakcc@4.4.0';
const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const dry = args.includes('--dry-run');
const noApply = args.includes('--no-apply') || dry;
const di = args.indexOf('--dir');
const dir = di >= 0 ? args[di + 1]
  : path.join(process.env.TWEAKCC_CONFIG_DIR || path.join(os.homedir(), '.tweakcc'), 'system-prompts');

const tsv = fs.readFileSync(path.join(here, 'tri-prompts.tsv'), 'utf8').split(/\r?\n/).slice(1).filter(Boolean);
const targets = tsv.map(l => l.split('\t')).filter(([, c]) => c === 'RETIRER').map(([f]) => f);

let emptied = 0, already = 0, missing = [];
for (const f of targets) {
  const p = path.join(dir, f);
  if (!fs.existsSync(p)) { missing.push(f); continue; }
  const txt = fs.readFileSync(p, 'utf8');
  const m = txt.match(/^<!--[\s\S]*?-->/);
  if (!m) { console.error(`en-tête tweakcc introuvable : ${f}`); process.exit(2); }
  // Si l'en-tête déclare des variables, tweakcc exige qu'elles restent citées dans un ${…},
  // sinon il croit le fichier périmé et signale un conflit à chaque --apply.
  // ${(A,B,"")} les cite sans rien produire : la chaîne injectée reste vide.
  const vars = [...(m[0].match(/^variables:\s*\n((?:\s+-\s+.*\n?)+)/m)?.[1] ?? '').matchAll(/-\s+(\S+)/g)].map(x => x[1]);
  const out = m[0] + '\n' + (vars.length ? '${(' + vars.join(',') + ',"")}' : '');
  if (txt === out) { already++; continue; }
  if (!dry) fs.writeFileSync(p, out, 'utf8');
  emptied++;
}
console.log(`RETIRER : ${targets.length} ; vidés : ${emptied} ; déjà vides : ${already} ; absents : ${missing.length}`);
if (missing.length) console.log('absents (fragment disparu de cette version ?) :\n  ' + missing.join('\n  '));
if (dry) console.log('(dry-run : rien écrit)');

if (!noApply) {
  // tweakcc cherche `claude` dans le PATH : la commande renommée en `agent` par ABC lui est indiquée
  // par TWEAKCC_CC_INSTALLATION_PATH (sauf si l'appelant l'a déjà posée, ou si ccInstallationPath la fixe).
  const env = { ...process.env };
  if (!env.TWEAKCC_CC_INSTALLATION_PATH) {
    const bin = path.join(os.homedir(), '.local', 'bin');
    const exe = process.platform === 'win32' ? '.exe' : '';
    const cli = env.ABC_CLI || 'agent';
    const found = [cli, 'claude'].map(n => path.join(bin, n + exe)).find(p => fs.existsSync(p));
    if (found) { env.TWEAKCC_CC_INSTALLATION_PATH = found; console.log(`binaire visé : ${found}`); }
  }
  const r = spawnSync('npx', ['-y', TWEAKCC, '--apply', '--yes'], { stdio: 'inherit', shell: process.platform === 'win32', env });
  process.exit(r.status ?? 1);
}
