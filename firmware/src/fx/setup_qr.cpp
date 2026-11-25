// "Get the app" QR code for a device no host has talked to since it booted. See setup_qr.h.
#include "setup_qr.h"
#include "../core/sys.h"
#include <lvgl.h>
#include "../ui/theme.h"
#include "../core/model.h"

// 31 bytes at ECC M is a version 3 code, 29 modules: 6 px each, inside the 4-module quiet zone the spec asks for.
static const int MODULE_PX = 6, MODULES = 29, QUIET_PX = 4 * MODULE_PX;

static lv_obj_t *root;            // null while hidden: built on demand, deleted for good on the first state
static bool host_seen = false;    // latched for the whole boot

static void build() {
  // a card over whatever tile shows: the room stays visible around it, touches outside it reach the tiles
  root = lv_obj_create(lv_layer_top());
  lv_obj_remove_style_all(root);
  lv_obj_set_size(root, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
  lv_obj_set_style_bg_color(root, C_BG, 0);
  lv_obj_set_style_bg_opa(root, LV_OPA_COVER, 0);
  lv_obj_set_style_border_color(root, C_BORDER, 0);
  lv_obj_set_style_border_width(root, 2, 0);
  lv_obj_set_style_radius(root, 18, 0);
  lv_obj_set_style_pad_all(root, 16, 0);
  lv_obj_set_style_pad_row(root, 12, 0);
  lv_obj_set_flex_flow(root, LV_FLEX_FLOW_COLUMN);
  lv_obj_set_flex_align(root, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
  lv_obj_add_flag(root, LV_OBJ_FLAG_CLICKABLE);
  lv_obj_clear_flag(root, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_GESTURE_BUBBLE);

  lv_obj_t *title = lv_label_create(root);
  lv_obj_set_style_text_font(title, F_BODY, 0);
  lv_obj_set_style_text_color(title, C_TEXT, 0);
  lv_label_set_text(title, "Get the companion app");

  lv_obj_t *card = lv_obj_create(root);
  lv_obj_remove_style_all(card);
  lv_obj_set_size(card, MODULES * MODULE_PX + 2 * QUIET_PX, MODULES * MODULE_PX + 2 * QUIET_PX);
  lv_obj_set_style_bg_color(card, C_TEXT, 0);
  lv_obj_set_style_bg_opa(card, LV_OPA_COVER, 0);
  lv_obj_set_style_radius(card, 10, 0);
  lv_obj_clear_flag(card, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *qr = lv_qrcode_create(card, MODULES * MODULE_PX, C_BG, C_TEXT);
  lv_qrcode_update(qr, SETUP_QR_URL, strlen(SETUP_QR_URL));
  lv_obj_center(qr);

  lv_obj_t *url = lv_label_create(root);
  lv_obj_set_style_text_font(url, F_SMALL, 0);
  lv_obj_set_style_text_color(url, C_ACCENT2, 0);
  lv_label_set_text(url, SETUP_QR_URL + strlen("https://"));

  lv_obj_center(root);
}

void setup_qr_tick() {
  if (host_seen) return;
  if (model_state_version()) {    // the first state of this boot
    host_seen = true;
    if (root) { lv_obj_del(root); root = nullptr; }
    return;
  }
  if (!root && millis() >= SETUP_QR_AFTER_MS) build();
}
