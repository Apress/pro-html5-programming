/*
 * Track and report the current location
 */
var handlePositionUpdate = function(e) {
    var latitude = e.coords.latitude;
    var longitude = e.coords.longitude;
    log("Position update:", latitude, longitude);
    if(navigator.onLine) {
        uploadLocations(latitude, longitude);
    }
    storeLocation(latitude, longitude);
}

var handlePositionError = function(e) {
    log("Position error");
}

var uploadLocations = function(latitude, longitude) {
    var request = new XMLHttpRequest();
    request.open("POST", "http://geodata.example.net:8000/geoupload", true);
    request.send(localStorage.locations);
}

var storeLocation = function(latitude, longitude) {
    // load stored location list
    var locations = JSON.parse(localStorage.locations || "[]");
    // add location
    locations.push({"latitude" : latitude, "longitude" : longitude});
    // save new location list
    localStorage.locations = JSON.stringify(locations);
}

var geolocationConfig = {"maximumAge":20000};

navigator.geolocation.watchPosition(handlePositionUpdate,
                                    handlePositionError,
                                    geolocationConfig);

