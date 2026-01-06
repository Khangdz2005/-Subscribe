#!/usr/bin/env node
/**
 * Minimal JSEncrypt (RSA) sandbox.
 *
 * Usage:
 *   node encrypt.js --pub ./public.pem --data '{"hello":"world"}'
 *   node encrypt.js --pub ./public.pem --data-file ./payload.json
 *
 * Output:
 *   Prints base64 ciphertext (string) or exits non-zero on failure.
 */

const fs = require("node:fs");
const path = require("node:path");

function usageAndExit(code) {
  const msg = `
Usage:
  node encrypt.js --pub <public.pem> --data <string>
  node encrypt.js --pub <public.pem> --data-file <file>

Notes:
  - Public key should be PEM format (-----BEGIN PUBLIC KEY----- ...).
  - Output is base64 ciphertext (like JSEncrypt.encrypt()).
`;
  process.stderr.write(msg.trimStart());
  process.exit(code);
}

function readArg(name) {
  const idx = process.argv.indexOf(name);
  if (idx === -1) return null;
  const v = process.argv[idx + 1];
  if (!v || v.startsWith("--")) return null;
  return v;
}

const pubPath = readArg("--pub");
const data = readArg("--data");
const dataFile = readArg("--data-file");

if (!pubPath || (!data && !dataFile) || (data && dataFile)) {
  usageAndExit(2);
}

const pubPem = fs.readFileSync(path.resolve(pubPath), "utf8").trim();
const plaintext = data
  ? data
  : fs.readFileSync(path.resolve(dataFile), "utf8").toString();

// jsencrypt package exports { JSEncrypt } and default in some bundlers.
// Require defensively.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const jsencrypt = require("jsencrypt");
const JSEncrypt = jsencrypt.JSEncrypt || jsencrypt.default || jsencrypt;

const crypt = new JSEncrypt({});
crypt.setPublicKey(pubPem);
const encrypted = crypt.encrypt(plaintext);

if (!encrypted) {
  process.stderr.write(
    "Encrypt failed. Check key format and plaintext length.\n"
  );
  process.exit(1);
}

// Avoid crashing when output is piped to a command
// that closes early (e.g. `head -c 80`).
process.stdout.on("error", (err) => {
  if (err && err.code === "EPIPE") process.exit(0);
  throw err;
});

process.stdout.write(String(encrypted));

