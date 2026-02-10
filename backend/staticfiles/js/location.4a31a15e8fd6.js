let latitude = null;
let longitude = null;
let locationSource = "auto";

function detectLocation() {
  if (!navigator.geolocation) {
    showManualOption();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      latitude = position.coords.latitude;
      longitude = position.coords.longitude;
      locationSource = "auto";

      console.log("Auto location:", latitude, longitude);
      fillHiddenFields();
    },
    (error) => {
      console.log("Auto detect failed");
      showManualOption();
    },
    {
      enableHighAccuracy: true,
      timeout: 8000
    }
  );

  // fallback if it hangs
  setTimeout(showManualOption, 8000);
}
