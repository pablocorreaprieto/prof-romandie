// Remembers ticked checklist items in this browser only. Nothing leaves the device.
(function () {
  var lists = document.querySelectorAll("ul.checklist[data-key]");
  for (var n = 0; n < lists.length; n++) {
    (function (ul) {
      var key = "prof-romandie:" + ul.getAttribute("data-key");
      var state = {};
      try { state = JSON.parse(window.localStorage.getItem(key) || "{}") || {}; } catch (e) { state = {}; }
      var boxes = ul.querySelectorAll('input[type="checkbox"]');
      for (var i = 0; i < boxes.length; i++) {
        (function (box, idx) {
          if (state[idx]) box.checked = true;
          box.addEventListener("change", function () {
            state[idx] = box.checked;
            try { window.localStorage.setItem(key, JSON.stringify(state)); } catch (e) { /* storage unavailable */ }
          });
        })(boxes[i], i);
      }
    })(lists[n]);
  }
})();
