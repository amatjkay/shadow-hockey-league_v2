#!/usr/bin/env node
// MCP Context Server - Fixed Implementation
const readline = require("readline");

let initialized = false;

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on("line", (line) => {
  try {
    const msg = JSON.parse(line);
    if (msg.method === "initialize" && !initialized) {
      initialized = true;
      process.stdout.write(JSON.stringify({
        jsonrpc: "2.0",
        id: msg.id,
        result: {
          capabilities: { handlesContext: true }
        }
      }) + "
");
    }
  } catch(e) {};
});

console.error("Context server ready");
