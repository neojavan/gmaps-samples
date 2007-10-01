function newMarker(lat, lng, name) {
  var marker = new GMarker(new GLatLng(lat, lng));
  GEvent.addListener(marker, "click", function() {
    marker.openInfoWindowHtml(name);
  });
  return marker;
}
map.setCenter(new GLatLng(22.97, 78.05), 5);
map.addOverlay(
    newMarker(28.63, 77.21, "New Delhi"));
