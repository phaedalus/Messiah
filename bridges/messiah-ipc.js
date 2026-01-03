const net = require("net");
const crypto = require("crypto");

const DEFAULT_HOST = process.env.MESSIAH_HOST || "127.0.0.1";
const DEFAULT_PORT = 42207;

/**
 * Send a single command to the Messiah runtime.
 *
 * @param {string} cmd - Command name
 * @param {object} data - Extra payload fields
 * @param {object} options - { host, port, timeout }
 * @returns {Promise<object>} Parsed JSON response
 */

function sendMessiahCommand(cmd, data = {}, options = {}) {
  const host = options.host || DEFAULT_HOST;
  const port = options.port || DEFAULT_PORT;
  const timeout = options.timeout || 5000;

  const request = {
    request_id: crypto.randomUUID(),
    cmd,
    ...data,
  };

  return new Promise((resolve, reject) => {
    const socket = new net.Socket();
    let buffer = "";

    socket.setTimeout(timeout);

    socket.connect(port, host, () => {
      socket.write(JSON.stringify(request) + "\n");
    });

    socket.on("data", (chunk) => {
      buffer += chunk.toString("utf8");

      if (buffer.includes("\n")) {
        try {
          const response = JSON.parse(buffer.trim());
          resolve(response);
        } catch (err) {
          reject(new Error("Invalid JSON response"));
        } finally {
          socket.end();
        }
      }
    });

    socket.on("timeout", () => {
      socket.destroy();
      reject(new Error("Messiah runtime timed out"));
    });

    socket.on("error", (err) => {
      reject(err);
    });
  });
}

module.exports = { sendMessiahCommand };