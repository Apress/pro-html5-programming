importScripts("blur.js");

function sendStatus(statusText) {
    postMessage({"type" : "status",
                 "statusText" : statusText}
                );
}

function messageHandler(e) {
    var messageType = e.data.type;
    switch (messageType) {
        case ("blur"):
            sendStatus("Worker started blur on data in range: " +
                            e.data.startX + "-" + (e.data.startX+e.data.width));
            var imageData = e.data.imageData;
            imageData = boxBlur(imageData, e.data.width, e.data.height, e.data.startX);

            postMessage({"type" : "progress",
                         "imageData" : imageData,
                         "width" : e.data.width,
                         "height" : e.data.height,
                         "startX" : e.data.startX
                        });
            sendStatus("Finished blur on data in range: " +
                            e.data.startX + "-" + (e.data.width+e.data.startX));
            break;
        default:
            sendStatus("Worker got message: " + e.data);
    }
}

addEventListener("message", messageHandler, true);

