#pragma once
// "Get the app" code: a device that powered up and never heard from the companion app shows a QR code to the
// GitHub repo, in a card over the current tile, until the first `state` arrives. (setup_qr.cpp)
//
//  boot --(SETUP_QR_AFTER_MS without a state)--> QR shown --(first state)--> gone until the next boot
//
// Once a host has talked on this boot the code never comes back: a computer that sleeps or shuts down with the
// USB port still powered leaves the usual offline screens and night clock (fx/ambient.cpp) untouched.
// It sits above the night clock on lv_layer_top(); the tiles around it stay usable, the backlight still dims.
// `tools/dev.py shot --nodemo` sends no state, so it can photograph the code.
#define SETUP_QR_AFTER_MS 10000   // the app finds a freshly plugged device within ~2-4 s: no flash of the code
#define SETUP_QR_URL "https://github.com/d-weber/SQRM8"

void setup_qr_tick();             // call from the UI loop
