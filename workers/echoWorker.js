function messageHandler(e) {
  postMessage("worker says: " + e.data + " too");
}

addEventListener("message", messageHandler, true);
