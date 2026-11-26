"use strict";

const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const source = path.join(root, "manuscript", "figures");
const output = path.join(root, "submission", "jisa", "figures-png");
fs.mkdirSync(output, { recursive: true });

const names = [
  "figure-1-latency",
  "figure-2-communication",
  "figure-3-network-sensitivity",
  "figure-s1-primary-batches",
  "figure-s2-compatibility-matrix",
];

Promise.all(names.map(async (name) => {
  await sharp(path.join(source, `${name}.svg`), { density: 220 })
    .png()
    .toFile(path.join(output, `${name}.png`));
})).then(() => process.stdout.write("JISA figures rasterized\n"));
